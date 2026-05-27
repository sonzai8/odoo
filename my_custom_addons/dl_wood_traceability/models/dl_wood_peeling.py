# -*- coding: utf-8 -*-
"""
Quản lý Hồ Sơ Ván Bóc & Hoá Đơn Ván Bóc.
NCC ván bóc mua gỗ tươi → chế biến thành ván bóc → bán lại cho công ty.
Mỗi lần bán = 1 hoá đơn. Nhiều hoá đơn thuộc 1 bộ hồ sơ to.
Trừ lùi nguyên liệu dựa trên hoá đơn (FIFO).
"""
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  HỒ SƠ VÁN BÓC (Bộ hồ sơ to — gom nhiều hoá đơn)                        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class DlWoodPeelingDossier(models.Model):
    """Hồ sơ ván bóc — quản lý bộ hồ sơ gốc mà NCC mua gỗ về chế biến."""
    _name = 'dl.wood.peeling.dossier'
    _description = 'Hồ Sơ Ván Bóc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    # ── Display name ──────────────────────────────────────────────────────────
    @api.depends('name', 'partner_id.name', 'qty_available')
    def _compute_display_name(self):
        for rec in self:
            partner_name = rec.partner_id.name or 'Không có NCC'
            qty_avail = rec.qty_available or 0.0
            rec.display_name = f"{rec.name} - {partner_name} - {qty_avail:.2f} m³"

    @api.model
    def _get_default_name(self):
        """Tự động sinh mã hồ sơ: HSV_0001, HSV_0002..."""
        prefix = self.env.company.x_wood_prefix or "XX"
        count = self.search_count([('company_id', '=', self.env.company.id)])
        return f"{prefix}_HSV_{(count + 1):04d}"

    # ── Thông tin cơ bản ──────────────────────────────────────────────────────
    name = fields.Char(
        string='Mã Hồ Sơ', required=True, copy=False,
        readonly=True, default=_get_default_name, index=True
    )
    x_dossier_name = fields.Char(
        string='Tên Hồ Sơ',
        help='Tên mô tả ngắn gọn cho bộ hồ sơ ván bóc'
    )
    partner_id = fields.Many2one(
        'res.partner', string='Nhà Cung Cấp',
        required=True,
        domain="[('x_is_peeling_supplier', '=', True), ('is_company', '=', True), "
               "'|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        tracking=True
    )
    date_received = fields.Date(
        string='Ngày nhận hồ sơ',
        default=fields.Date.context_today,
        tracking=True
    )
    company_id = fields.Many2one(
        'res.company', string='Công ty',
        required=True, default=lambda self: self.env.company, index=True
    )
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id',
        string='Tiền tệ', readonly=True
    )
    note = fields.Text(string='Ghi chú')

    # ── Thông tin chủ rừng (Liên kết hoặc nhập tay) ───────────────────────────
    x_forest_owner_id = fields.Many2one(
        'res.partner',
        string='Chủ Rừng / Khai thác',
        domain="[('x_is_wood_supplier', '=', 'owner')]",
        help="Chọn chủ rừng để tự động lấy thông tin"
    )
    x_exploitation_location_id = fields.Many2one(
        'dl.wood.exploitation.location', 
        string='Chọn Nơi khai thác',
        domain="[('partner_id', '=', x_forest_owner_id)]"
    )

    x_forest_owner_name = fields.Char(
        related='x_forest_owner_id.name',
        string='Tên chủ rừng',
        store=True,
        readonly=False
    )
    x_forest_owner_cccd = fields.Char(
        related='x_forest_owner_id.x_cccd',
        string='Số CCCD chủ rừng',
        store=True,
        readonly=False
    )
    x_forest_owner_address = fields.Char(
        related='x_forest_owner_id.x_full_address',
        string='Địa chỉ chủ rừng',
        store=True,
        readonly=False
    )
    x_forest_owner_phone = fields.Char(
        related='x_forest_owner_id.phone',
        string='SĐT chủ rừng',
        store=True,
        readonly=False
    )
    x_exploitation_address = fields.Char(
        related='x_exploitation_location_id.full_address',
        string='Địa danh khai thác',
        store=True,
        readonly=False
    )
    x_exploitation_area = fields.Float(
        related='x_exploitation_location_id.x_area_ha',
        string='Diện tích khai thác (ha)',
        digits=(16, 2),
        store=True,
        readonly=False
    )

    @api.onchange('x_forest_owner_id')
    def _onchange_x_forest_owner_id_clear_location(self):
        if self.x_exploitation_location_id and self.x_exploitation_location_id.partner_id != self.x_forest_owner_id:
            self.x_exploitation_location_id = False

    # ── Trạng thái ────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('using', 'Đang dùng'),
        ('done', 'Hết'),
    ], string='Trạng thái', default='draft', index=True, tracking=True)

    # ── Hoá đơn ván bóc ──────────────────────────────────────────────────────
    invoice_ids = fields.One2many(
        'dl.wood.peeling.invoice', 'dossier_id',
        string='Hoá đơn ván bóc'
    )
    production_line_ids = fields.One2many(
        'dl.wood.peeling.production.line', 'peeling_dossier_id',
        string='Lịch sử sử dụng'
    )
    invoice_count = fields.Integer(
        string='Số hoá đơn',
        compute='_compute_invoice_count'
    )

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    # ── Tổng hợp khối lượng (compute từ hoá đơn) ─────────────────────────────
    qty_initial = fields.Float(
        string='Tổng KL ban đầu (m³)',
        compute='_compute_qty_totals', store=True, digits=(16, 2)
    )
    qty_used = fields.Float(
        string='Tổng KL đã dùng (m³)',
        compute='_compute_qty_totals', store=True, digits=(16, 2)
    )
    qty_available = fields.Float(
        string='Tổng tồn khả dụng (m³)',
        compute='_compute_qty_totals', store=True, digits=(16, 2)
    )
    x_total_cost = fields.Float(
        string='Tổng giá trị (VND)',
        compute='_compute_qty_totals', store=True, digits=(16, 2)
    )

    @api.depends('invoice_ids.qty_initial', 'invoice_ids.qty_used',
                 'invoice_ids.qty_available', 'invoice_ids.x_subtotal')
    def _compute_qty_totals(self):
        for rec in self:
            rec.qty_initial = sum(rec.invoice_ids.mapped('qty_initial'))
            rec.qty_used = sum(rec.invoice_ids.mapped('qty_used'))
            rec.qty_available = sum(rec.invoice_ids.mapped('qty_available'))
            rec.x_total_cost = sum(rec.invoice_ids.mapped('x_subtotal'))

    # ── Tài liệu PDF ─────────────────────────────────────────────────────────
    x_contract_attachment_ids = fields.Many2many(
        'ir.attachment',
        'dl_peeling_dossier_contract_attachment_rel',
        'dossier_id', 'attachment_id',
        string='Hợp đồng mua bán'
    )
    x_bkls_attachment_ids = fields.Many2many(
        'ir.attachment',
        'dl_peeling_dossier_bkls_attachment_rel',
        'dossier_id', 'attachment_id',
        string='Bảng kê lâm sản'
    )

    # ── Actions chuyển trạng thái ─────────────────────────────────────────────
    def action_confirm(self):
        """Chuyển sang trạng thái 'Đang dùng'."""
        for rec in self:
            if not rec.invoice_ids:
                raise UserError(_('Vui lòng thêm ít nhất 1 hoá đơn ván bóc trước khi xác nhận.'))
            rec.state = 'using'

    def action_done(self):
        """Chuyển sang trạng thái 'Hết'."""
        for rec in self:
            rec.state = 'done'

    def action_draft(self):
        """Quay về trạng thái 'Dự thảo'."""
        for rec in self:
            rec.state = 'draft'

    def action_open_import_invoice_wizard(self):
        self.ensure_one()
        return {
            'name': _('Nhập Hoá Đơn Ván Bóc'),
            'type': 'ir.actions.act_window',
            'res_model': 'dl.wood.peeling.invoice.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_dossier_id': self.id,
            }
        }

    def action_view_invoices(self):
        """Mở danh sách hoá đơn của hồ sơ này."""
        self.ensure_one()
        return {
            'name': _('Hoá đơn - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'dl.wood.peeling.invoice',
            'view_mode': 'list,form',
            'domain': [('dossier_id', '=', self.id)],
            'context': {'default_dossier_id': self.id},
        }


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  HOÁ ĐƠN VÁN BÓC (Đơn vị trừ lùi — thay thế dossier_line cũ)            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class DlWoodPeelingInvoice(models.Model):
    """Hoá đơn ván bóc — mỗi lần NCC bán ván bóc sẽ xuất 1 hoá đơn.
    Đây là đơn vị trừ lùi khi sản xuất (thay thế dossier_line cũ).
    """
    _name = 'dl.wood.peeling.invoice'
    _description = 'Hoá Đơn Ván Bóc'
    _order = 'invoice_date asc, id asc'

    # ── Display name ──────────────────────────────────────────────────────────
    @api.depends('invoice_number', 'partner_id.name', 'qty_available')
    def _compute_display_name(self):
        for rec in self:
            inv_num = rec.invoice_number or rec.name or '???'
            qty = rec.qty_available or 0.0
            rec.display_name = f"{inv_num} ({qty:.2f} m³)"

    # ── Thông tin cơ bản ──────────────────────────────────────────────────────
    name = fields.Char(
        string='Mã nội bộ', readonly=True, copy=False, index=True,
        default=lambda self: _('Mới')
    )
    invoice_number = fields.Char(
        string='Số hoá đơn', required=True, index=True,
        help='Số hoá đơn do NCC ván bóc cấp (VD: HĐ-001/2026)'
    )
    invoice_date = fields.Date(
        string='Ngày hoá đơn', required=True,
        default=fields.Date.context_today
    )
    dossier_id = fields.Many2one(
        'dl.wood.peeling.dossier', string='Hồ Sơ Ván Bóc',
        required=True, ondelete='cascade', index=True
    )
    dossier_code = fields.Char(
        string='Mã Hồ Sơ',
        related='dossier_id.name', store=True, index=True
    )
    partner_id = fields.Many2one(
        'res.partner', string='Nhà Cung Cấp',
        related='dossier_id.partner_id', store=True, index=True
    )
    forest_owner_name = fields.Char(
        string='Chủ rừng',
        related='dossier_id.x_forest_owner_name', store=True
    )
    company_id = fields.Many2one(
        'res.company', string='Công ty',
        related='dossier_id.company_id', store=True, index=True
    )
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id',
        string='Tiền tệ', readonly=True
    )

    # ── Khối lượng & giá ─────────────────────────────────────────────────────
    qty_initial = fields.Float(
        string='Khối lượng (m³)', digits=(16, 2), required=True,
        help='Khối lượng ván bóc ghi trên hoá đơn.'
    )
    qty_used = fields.Float(
        string='Đã dùng (m³)', digits=(16, 2), default=0.0,
        help='Khối lượng đã tiêu hao trong sản xuất (cộng dồn khi trừ lùi).'
    )
    qty_available = fields.Float(
        string='Tồn khả dụng (m³)',
        compute='_compute_qty_available', store=True, digits=(16, 2)
    )
    price_unit = fields.Float(
        string='Đơn giá (VND/m³)', digits=(16, 2),
        help='Đơn giá mua ván bóc theo hoá đơn.'
    )
    x_subtotal = fields.Float(
        string='Thành tiền (VND)',
        compute='_compute_x_subtotal', store=True, digits=(16, 2)
    )
    bkls_number = fields.Char(
        string='Số BKLS',
        help='Số bảng kê lâm sản chia nhỏ kèm hoá đơn (VD: 001/2026/BKLS)'
    )

    # ── Trạng thái (auto compute) ────────────────────────────────────────────
    state = fields.Selection([
        ('available', 'Còn hàng'),
        ('partial', 'Đã dùng 1 phần'),
        ('depleted', 'Đã hết'),
    ], string='Trạng thái', compute='_compute_state', store=True, index=True)

    @api.depends('qty_initial', 'qty_used')
    def _compute_qty_available(self):
        for rec in self:
            rec.qty_available = max(0.0, rec.qty_initial - rec.qty_used)

    @api.depends('qty_initial', 'price_unit')
    def _compute_x_subtotal(self):
        for rec in self:
            rec.x_subtotal = round(rec.qty_initial * rec.price_unit, 2)

    @api.depends('qty_initial', 'qty_used')
    def _compute_state(self):
        for rec in self:
            if rec.qty_used <= 0:
                rec.state = 'available'
            elif rec.qty_used >= rec.qty_initial:
                rec.state = 'depleted'
            else:
                rec.state = 'partial'

    @api.model_create_multi
    def create(self, vals_list):
        """Tự động sinh mã nội bộ khi tạo hoá đơn."""
        for vals in vals_list:
            if vals.get('name', _('Mới')) == _('Mới'):
                company_id = vals.get('company_id') or self.env.company.id
                if not company_id and vals.get('dossier_id'):
                    dossier = self.env['dl.wood.peeling.dossier'].browse(vals['dossier_id'])
                    company_id = dossier.company_id.id or self.env.company.id
                company = self.env['res.company'].browse(company_id)
                prefix = company.x_wood_prefix or "XX"
                count = self.search_count([('company_id', '=', company_id)])
                vals['name'] = f"{prefix}_PB_HD_{(count + 1):04d}"
        return super().create(vals_list)
