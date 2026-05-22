# -*- coding: utf-8 -*-
"""
dl.wood.dossier.inventory - Kiểm Kê Hồ Sơ Gỗ (Stocktaking & Adjustment)
Mục đích: Rà soát khối lượng tồn thực tế của các bộ hồ sơ gỗ nguồn định kỳ.
Cho phép điều chỉnh chênh lệch khối lượng và rollback an toàn qua Sổ cái (Ledger).
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class DlWoodDossierInventory(models.Model):
    _name = 'dl.wood.dossier.inventory'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Phiếu Kiểm Kê Hồ Sơ Gỗ'
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Mã Kiểm Kê',
        required=True,
        readonly=True,
        copy=False,
        default='/'
    )
    date = fields.Date(
        string='Ngày Kiểm Kê',
        default=fields.Date.context_today,
        required=True,
        help='Ngày thực hiện kiểm kê rà soát.'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Công ty',
        required=True,
        default=lambda self: self.env.company,
        index=True
    )
    note = fields.Text(
        string='Lý do điều chỉnh ',
        help='Mô tả ngắn gọn lý do chênh lệch hoặc ghi chú kiểm kê.'
    )
    x_inspector = fields.Char(
        string='Người kiểm kê',
        default=lambda self: self.env.company.x_inventory_inspector or ''
    )
    x_inspector_position = fields.Char(
        string='Chức danh người kiểm kê',
        default=lambda self: self.env.company.x_inventory_inspector_position or ''
    )
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('review', 'Rà soát'),
        ('done', 'Hoàn thành'),
        ('cancel', 'Đã hủy')
    ], string='Trạng thái', default='draft', required=True, tracking=True)

    line_ids = fields.One2many(
        'dl.wood.dossier.inventory.line',
        'inventory_id',
        string='Chi tiết điều chỉnh',
        copy=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                company_id = vals.get('company_id') or self.env.company.id
                company = self.env['res.company'].browse(company_id)
                prefix = company.x_wood_prefix or 'QTP'
                seq = self.env['ir.sequence'].with_company(company).next_by_code('dl.wood.dossier.inventory') or ''
                vals['name'] = f"{prefix}{seq}"
        return super(DlWoodDossierInventory, self).create(vals_list)

    def action_draft(self):
        """Đưa phiếu kiểm kê về trạng thái dự thảo."""
        self.ensure_one()
        if self.state not in ('review', 'cancel'):
            raise UserError(_('Không thể đưa về dự thảo từ trạng thái hiện tại.'))
        self.state = 'draft'
        return True

    def action_review(self):
        """Gửi phiếu kiểm kê đi rà soát duyệt."""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Chỉ phiếu ở trạng thái Dự thảo mới có thể gửi rà soát.'))
        if not self.line_ids:
            raise UserError(_('Vui lòng thêm ít nhất một dòng chi tiết để kiểm kê.'))
        self.state = 'review'
        return True

    def action_done(self):
        """
        Xác nhận hoàn thành kiểm kê:
        Tạo các bản ghi Ledger (Sổ cái) để điều chỉnh tồn kho cho các loài gỗ có chênh lệch.
        """
        self.ensure_one()
        if self.state != 'review':
            raise UserError(_('Chỉ phiếu kiểm kê ở trạng thái Rà soát mới được phép Duyệt hoàn thành.'))

        # Kiểm tra lý do điều chỉnh bắt buộc nếu có chênh lệch khối lượng
        if not self.note:
            has_diff = any(abs(line.adjusted_volume) > 0.0001 for line in self.line_ids)
            if has_diff:
                raise UserError(_('Có sự chênh lệch khối lượng gỗ thực tế. Vui lòng nhập "Lý do điều chỉnh / Ghi chú" trước khi hoàn thành.'))

        for line in self.line_ids:
            # Chỉ tạo Ledger khi có khối lượng điều chỉnh thực tế
            if abs(line.adjusted_volume) > 0.0001:
                # Tạo bản ghi Sổ cái (Ledger) tương ứng
                ledger = self.env['dl.dossier.ledger'].create({
                    'dossier_id': line.dossier_id.id,
                    'species_id': line.species_id.id,
                    'actual_qty': line.adjusted_volume,
                    'state': 'done',
                    'date': fields.Datetime.now(),
                    'inventory_line_id': line.id,
                })
                line.ledger_id = ledger.id
                
                # Ép dossier recompute lại tồn kho ngay lập tức
                line.dossier_id._compute_stock_quantities()

        self.state = 'done'
        return True

    def action_cancel(self):
        """
        Hủy bỏ hiệu lực của lần kiểm kê (Rollback):
        Xóa bỏ toàn bộ các bản ghi Sổ cái đã sinh ra trong phiếu này, giúp khôi phục tồn kho gỗ chính xác.
        """
        self.ensure_one()
        if self.state != 'done':
            raise UserError(_('Chỉ phiếu đã Hoàn thành mới hỗ trợ hủy bỏ (Rollback).'))

        # Tìm các ledger đã tạo từ dòng của phiếu kiểm kê này
        ledgers_to_unlink = self.line_ids.mapped('ledger_id')
        dossiers_to_recompute = self.line_ids.mapped('dossier_id')

        if ledgers_to_unlink:
            # Xóa sạch các ledger để hoàn trả tồn kho hoàn hảo
            ledgers_to_unlink.unlink()
            _logger.info(f"Rollback kiểm kê {self.name}: Đã xóa {len(ledgers_to_unlink)} bản ghi Ledger điều chỉnh.")

        # Reset liên kết ledger trên dòng
        self.line_ids.write({'ledger_id': False})

        # Cập nhật lại tồn kho của các hồ sơ liên quan
        for dossier in dossiers_to_recompute:
            dossier._compute_stock_quantities()

        self.state = 'cancel'
        return True


class DlWoodDossierInventoryLine(models.Model):
    _name = 'dl.wood.dossier.inventory.line'
    _description = 'Chi Tiết Điều Chỉnh Kiểm Kê'

    inventory_id = fields.Many2one(
        'dl.wood.dossier.inventory',
        string='Phiếu Kiểm Kê',
        ondelete='cascade',
        required=True
    )
    company_id = fields.Many2one(
        'res.company',
        related='inventory_id.company_id',
        string='Công ty',
        store=True,
        index=True,
        readonly=True
    )
    state = fields.Selection(
        related='inventory_id.state',
        string='Trạng thái',
        readonly=True
    )
    dossier_id = fields.Many2one(
        'dl.wood.dossier',
        string='Hồ Sơ Gỗ',
        required=True,
        ondelete='cascade',
        domain="[('company_id', '=', company_id), ('state', '=', 'using')]"
    )
    x_partner_id = fields.Many2one(
        'res.partner',
        related='dossier_id.partner_id',
        string='Chủ Rừng',
        readonly=True,
        store=True
    )
    species_id = fields.Many2one(
        'dl.wood.species',
        string='Loài Gỗ/Củi',
        required=True,
        ondelete='restrict',
        domain="[('id', 'in', allowed_species_ids)]"
    )
    allowed_species_ids = fields.Many2many(
        'dl.wood.species',
        compute='_compute_allowed_species_ids',
        string='Các loài gỗ được phép chọn'
    )
    wood_type = fields.Selection(
        related='species_id.wood_type',
        string='Phân Loại',
        store=True,
        readonly=True
    )
    current_volume_species = fields.Float(
        string='Tồn Phần Mềm (m³)',
        compute='_compute_current_volume_species',
        store=False,
        digits=(16, 2),
        help='Tồn kho hiện tại của loài gỗ/củi này tính toán trên phần mềm.'
    )
    adjusted_volume = fields.Float(
        string='KL Điều Chỉnh (m³)',
        compute='_compute_adjusted_volume',
        store=True,
        digits=(16, 2),
        readonly=True,
        help='Lượng chênh lệch tự động tính toán (KL Thực Tế - Tồn Phần Mềm).'
    )
    new_volume = fields.Float(
        string='KL Thực Tế (m³)',
        digits=(16, 2),
        default=0.0,
        help='Khối lượng đếm thực tế của bộ hồ sơ.'
    )
    ledger_id = fields.Many2one(
        'dl.dossier.ledger',
        string='Bản Ghi Sổ Cái',
        ondelete='set null',
        readonly=True,
        copy=False
    )

    @api.depends('dossier_id')
    def _compute_allowed_species_ids(self):
        for line in self:
            if line.dossier_id:
                # Tìm các species_id có trong dossier
                species_ids = line.dossier_id.line_ids.mapped('species_id')
                line.allowed_species_ids = species_ids
            else:
                line.allowed_species_ids = self.env['dl.wood.species']

    @api.onchange('dossier_id', 'species_id')
    def _onchange_dossier_species(self):
        """
        Khi người dùng chọn Hồ sơ và Loài gỗ, tự động nạp lượng tồn thực tế x_remaining_qty
        hiện tại của loài gỗ đó trong Hồ sơ làm mặc định cho KL Thực Tế.
        """
        if self.dossier_id and self.species_id:
            dossier_db = self.dossier_id._origin or self.dossier_id
            species_db = self.species_id._origin or self.species_id
            
            d_line = dossier_db.line_ids.filtered(lambda l: l.species_id == species_db)
            self.new_volume = round(sum(d_line.mapped('x_remaining_qty')), 2)

    @api.depends('dossier_id', 'species_id', 'inventory_id.state')
    def _compute_current_volume_species(self):
        """
        Tính toán lượng tồn hiện tại của loài gỗ/củi trong hồ sơ:
        Lấy trực tiếp từ x_remaining_qty của hồ sơ gỗ nguồn.
        Nếu phiếu đã hoàn thành, cộng/trừ ngược lượng đã điều chỉnh từ Sổ cái (Ledger) để giữ nguyên số liệu audit trail lịch sử.
        """
        for line in self:
            if not line.dossier_id or not line.species_id:
                line.current_volume_species = 0.0
                continue

            dossier_db = line.dossier_id._origin or line.dossier_id
            species_db = line.species_id._origin or line.species_id
            
            d_line = dossier_db.line_ids.filtered(lambda l: l.species_id == species_db)
            current_vol = sum(d_line.mapped('x_remaining_qty'))

            if line.inventory_id.state == 'done' and line.ledger_id:
                line.current_volume_species = round(current_vol - line.ledger_id.actual_qty, 2)
            else:
                line.current_volume_species = round(current_vol, 2)

    @api.depends('new_volume', 'current_volume_species')
    def _compute_adjusted_volume(self):
        """Tự động tính chênh lệch: KL Thực Tế - Tồn Phần Mềm"""
        for line in self:
            line.adjusted_volume = round((line.new_volume or 0.0) - (line.current_volume_species or 0.0), 2)
