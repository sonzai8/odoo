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

    # Các trường thông tin chủ rừng đã được gỡ bỏ
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

    wood_dossier_id = fields.Many2one(
        'dl.wood.dossier',
        string='Nguồn gốc (Hồ sơ gỗ)',
        readonly=True,
        help='Hồ sơ gỗ nguồn mà từ đó sinh ra hồ sơ ván bóc này.'
    )
    wood_dossier_document_ids = fields.One2many(
        related='wood_dossier_id.document_ids',
        string='Tài liệu hồ sơ gỗ',
        readonly=True
    )

    # ── Hoá đơn ván bóc ──────────────────────────────────────────────────────
    invoice_ids = fields.One2many(
        'dl.wood.peeling.invoice', 'dossier_id',
        string='Hoá đơn ván bóc'
    )
    production_line_ids = fields.One2many(
        'dl.wood.peeling.production.line', 'peeling_dossier_id',
        string='Lịch sử sử dụng'
    )
    inventory_wood_ids = fields.One2many(
        'dl.wood.peeling.inventory.wood.summary', 'dossier_id',
        string='Tồn kho theo loài gỗ', readonly=True
    )
    inventory_variant_ids = fields.One2many(
        'dl.wood.peeling.inventory.variant.summary', 'dossier_id',
        string='Tồn kho theo loại ván bóc', readonly=True
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

            # Tự động cập nhật bảng thống kê tồn kho (Xoá cũ, tạo mới)
            rec.inventory_wood_ids.unlink()
            rec.inventory_variant_ids.unlink()
            
            wood_summary = {}
            variant_summary = {}
            
            for bkls_line in rec.invoice_ids.mapped('bkls_ids.line_ids'):
                variant = bkls_line.peeling_variant_id
                if not variant:
                    continue
                species = variant.peeling_type_id.species_id
                
                # Gom nhóm theo Variant
                if variant.id not in variant_summary:
                    variant_summary[variant.id] = {'qty_initial': 0.0, 'qty_available': 0.0, 'qty_used': 0.0}
                variant_summary[variant.id]['qty_initial'] += bkls_line.qty_initial
                variant_summary[variant.id]['qty_available'] += bkls_line.qty_available
                variant_summary[variant.id]['qty_used'] += bkls_line.qty_used
                
                # Gom nhóm theo Species
                species_id = species.id if species else False
                if species_id not in wood_summary:
                    wood_summary[species_id] = {'qty_initial': 0.0, 'qty_available': 0.0, 'qty_used': 0.0}
                wood_summary[species_id]['qty_initial'] += bkls_line.qty_initial
                wood_summary[species_id]['qty_available'] += bkls_line.qty_available
                wood_summary[species_id]['qty_used'] += bkls_line.qty_used

            if wood_summary:
                rec.inventory_wood_ids = [(0, 0, {
                    'species_id': sp_id,
                    'qty_initial': vals['qty_initial'],
                    'qty_available': vals['qty_available'],
                    'qty_used': vals['qty_used'],
                }) for sp_id, vals in wood_summary.items()]
                
            if variant_summary:
                rec.inventory_variant_ids = [(0, 0, {
                    'variant_id': var_id,
                    'qty_initial': vals['qty_initial'],
                    'qty_available': vals['qty_available'],
                    'qty_used': vals['qty_used'],
                }) for var_id, vals in variant_summary.items()]

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
    @api.depends('invoice_number', 'partner_id.name', 'qty_initial')
    def _compute_display_name(self):
        for rec in self:
            inv_num = rec.invoice_number or rec.name or '???'
            partner = rec.partner_id.name or 'Không NCC'
            rec.display_name = f"[{inv_num}] {partner} | Tổng: {rec.qty_initial:.2f} m³"

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = list(args or [])
        if name:
            domain = ['|', '|',
                ('invoice_number', operator, name),
                ('dossier_id.name', operator, name),
                ('bkls_ids.bkls_number', operator, name),
            ]
            from odoo.osv import expression
            args = expression.AND([args, domain])
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)

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
    company_id = fields.Many2one(
        'res.company', string='Công ty',
        related='dossier_id.company_id', store=True, index=True
    )
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id',
        string='Tiền tệ', readonly=True
    )

    # ── Phân loại ván bóc & loài gỗ (Tính từ BKLS) ──────────────────────────
    species_ids = fields.Many2many(
        'dl.wood.species',
        string='Các loài gỗ chứa trong Hóa đơn',
        compute='_compute_peeling_variant_names',
        store=True
    )
    x_peeling_variant_names = fields.Char(
        string='Loại ván bóc',
        compute='_compute_peeling_variant_names', store=True
    )
    x_wood_species_names = fields.Char(
        string='Loại gỗ',
        compute='_compute_peeling_variant_names', store=True
    )
    x_bkls_numbers = fields.Char(
        string='Số BKLS',
        compute='_compute_peeling_variant_names', store=True
    )

    # ── Khối lượng & giá (Tính tổng từ BKLS) ────────────────────────────────
    bkls_ids = fields.One2many(
        'dl.wood.peeling.bkls', 'invoice_id',
        string='Bảng kê lâm sản'
    )
    qty_initial = fields.Float(
        string='Khối lượng (m³)', compute='_compute_totals', store=True, digits=(16, 2),
        help='Tổng khối lượng ván bóc ghi trên hoá đơn.'
    )
    qty_used = fields.Float(
        string='Đã dùng (m³)', compute='_compute_totals', store=True, digits=(16, 2),
        help='Tổng khối lượng đã tiêu hao trong sản xuất.'
    )
    qty_available = fields.Float(
        string='Tồn khả dụng (m³)', compute='_compute_totals', store=True, digits=(16, 2)
    )
    x_subtotal = fields.Float(
        string='Thành tiền (VND)', compute='_compute_totals', store=True, digits=(16, 2)
    )

    # ── Trạng thái (auto compute) ────────────────────────────────────────────
    state = fields.Selection([
        ('available', 'Còn hàng'),
        ('partial', 'Đã dùng 1 phần'),
        ('depleted', 'Đã hết'),
    ], string='Trạng thái', compute='_compute_state', store=True, index=True)

    @api.depends('bkls_ids.line_ids.peeling_variant_id', 'bkls_ids.line_ids.peeling_variant_id.peeling_type_id.species_id', 'bkls_ids.bkls_number')
    def _compute_peeling_variant_names(self):
        for rec in self:
            variants = rec.bkls_ids.mapped('line_ids.peeling_variant_id')
            species = variants.mapped('peeling_type_id.species_id')
            bkls_nums = rec.bkls_ids.mapped('bkls_number')
            rec.x_peeling_variant_names = ', '.join(variants.mapped('name')) if variants else ''
            rec.x_wood_species_names = ', '.join(species.mapped('name')) if species else ''
            rec.x_bkls_numbers = ', '.join([b for b in bkls_nums if b]) if bkls_nums else ''
            rec.species_ids = species

    @api.depends('bkls_ids.qty_initial', 'bkls_ids.qty_used', 'bkls_ids.x_subtotal')
    def _compute_totals(self):
        for rec in self:
            rec.qty_initial = sum(rec.bkls_ids.mapped('qty_initial'))
            rec.qty_used = sum(rec.bkls_ids.mapped('qty_used'))
            rec.qty_available = sum(rec.bkls_ids.mapped('qty_available'))
            rec.x_subtotal = sum(rec.bkls_ids.mapped('x_subtotal'))

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
            if vals.get('dossier_id') and not self._context.get('skip_wood_dossier_check'):
                dossier = self.env['dl.wood.peeling.dossier'].browse(vals['dossier_id'])
                if dossier.wood_dossier_id:
                    raise UserError(_('Không thể thêm Hóa đơn ván bóc trực tiếp vào Hồ sơ được tạo từ Hồ sơ gỗ. Vui lòng quay lại Hồ sơ gỗ để bóc ván.'))
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

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  BẢNG KÊ LÂM SẢN VÁN BÓC (Nhóm các dòng chi tiết)                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class DlWoodPeelingBkls(models.Model):
    """Bảng kê lâm sản thuộc một Hoá đơn ván bóc."""
    _name = 'dl.wood.peeling.bkls'
    _description = 'Bảng kê lâm sản ván bóc'
    _order = 'bkls_date asc, bkls_number asc, id asc'

    @api.depends('bkls_number', 'qty_available')
    def _compute_display_name(self):
        for rec in self:
            bkls = rec.bkls_number or '???'
            qty = rec.qty_available or 0.0
            rec.display_name = f"BKLS {bkls} ({qty:.2f} m³)"

    invoice_id = fields.Many2one(
        'dl.wood.peeling.invoice', string='Hoá đơn',
        required=True, ondelete='cascade', index=True
    )
    bkls_number = fields.Char(
        string='Số BKLS', required=True,
        help='Số bảng kê lâm sản'
    )
    bkls_date = fields.Date(
        string='Ngày BKLS', required=True,
        default=fields.Date.context_today
    )
    line_ids = fields.One2many(
        'dl.wood.peeling.bkls.line', 'bkls_id',
        string='Chi tiết ván bóc'
    )

    # ── Khối lượng & giá ─────────────────────────────────────────────────────
    qty_initial = fields.Float(
        string='Khối lượng (m³)', compute='_compute_totals', store=True, digits=(16, 2)
    )
    qty_used = fields.Float(
        string='Đã dùng (m³)', compute='_compute_totals', store=True, digits=(16, 2)
    )
    qty_available = fields.Float(
        string='Tồn (m³)', compute='_compute_totals', store=True, digits=(16, 2)
    )
    x_subtotal = fields.Float(
        string='Thành tiền', compute='_compute_totals', store=True, digits=(16, 2)
    )

    state = fields.Selection([
        ('available', 'Còn hàng'),
        ('partial', 'Đã dùng 1 phần'),
        ('depleted', 'Đã hết'),
    ], string='Trạng thái', compute='_compute_state', store=True, index=True)

    @api.depends('line_ids.qty_initial', 'line_ids.qty_used', 'line_ids.x_subtotal')
    def _compute_totals(self):
        for rec in self:
            rec.qty_initial = sum(rec.line_ids.mapped('qty_initial'))
            rec.qty_used = sum(rec.line_ids.mapped('qty_used'))
            rec.qty_available = sum(rec.line_ids.mapped('qty_available'))
            rec.x_subtotal = sum(rec.line_ids.mapped('x_subtotal'))

    @api.depends('qty_initial', 'qty_used')
    def _compute_state(self):
        for rec in self:
            if rec.qty_used <= 0:
                rec.state = 'available'
            elif rec.qty_used >= rec.qty_initial:
                rec.state = 'depleted'
            else:
                rec.state = 'partial'


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  CHI TIẾT VÁN BÓC (Đơn vị trừ lùi thực tế)                                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class DlWoodPeelingBklsLine(models.Model):
    """Chi tiết loại ván bóc trong Bảng kê lâm sản."""
    _name = 'dl.wood.peeling.bkls.line'
    _description = 'Chi tiết ván bóc'
    _order = 'id asc'

    @api.depends('peeling_variant_id.name', 'qty_initial')
    def _compute_display_name(self):
        for rec in self:
            ptype = rec.peeling_variant_id.name or '???'
            qty = rec.qty_initial or 0.0
            rec.display_name = f"{ptype} (Tổng {qty:.2f} m³)"

    bkls_id = fields.Many2one(
        'dl.wood.peeling.bkls', string='Bảng kê lâm sản',
        required=True, ondelete='cascade', index=True
    )
    peeling_variant_id = fields.Many2one(
        'dl.wood.peeling.variant', string='Biến thể Ván Bóc',
        required=True, ondelete='restrict'
    )
    peeling_type_id = fields.Many2one(
        'dl.wood.peeling.type', string='Loại Ván Bóc',
        related='peeling_variant_id.peeling_type_id', store=True
    )
    invoice_id = fields.Many2one(
        'dl.wood.peeling.invoice', string='Số Hóa Đơn',
        related='bkls_id.invoice_id', store=True
    )
    dossier_id = fields.Many2one(
        'dl.wood.peeling.dossier', string='Hồ Sơ Ván Bóc',
        related='bkls_id.invoice_id.dossier_id', store=True
    )
    partner_id = fields.Many2one(
        'res.partner', string='Nhà Cung Cấp',
        related='bkls_id.invoice_id.partner_id', store=True
    )
    
    # ── Khối lượng & giá ─────────────────────────────────────────────────────
    qty_initial = fields.Float(
        string='Khối lượng (m³)', digits=(16, 2), required=True, default=0.0
    )
    qty_used = fields.Float(
        string='Đã dùng (m³)', digits=(16, 2), default=0.0
    )
    qty_available = fields.Float(
        string='Tồn (m³)', compute='_compute_qty_available', store=True, digits=(16, 2)
    )
    price_unit = fields.Float(
        string='Đơn giá (VND/m³)', digits=(16, 2)
    )
    x_subtotal = fields.Float(
        string='Thành tiền', compute='_compute_x_subtotal', store=True, digits=(16, 2)
    )

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

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  TỔNG HỢP TỒN KHO HỒ SƠ VÁN BÓC (Dùng cho tab Tồn kho)                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class DlWoodPeelingInventoryWoodSummary(models.Model):
    _name = 'dl.wood.peeling.inventory.wood.summary'
    _description = 'Thống kê tồn kho ván bóc theo loại gỗ'
    _order = 'qty_available desc, qty_initial desc'

    dossier_id = fields.Many2one('dl.wood.peeling.dossier', string='Hồ sơ', required=True, ondelete='cascade')
    species_id = fields.Many2one('dl.wood.species', string='Loài gỗ')
    qty_initial = fields.Float(string='Tổng Khối lượng (m³)', digits=(16, 2))
    qty_used = fields.Float(string='Đã sử dụng (m³)', digits=(16, 2))
    qty_available = fields.Float(string='Tồn khả dụng (m³)', digits=(16, 2))

class DlWoodPeelingInventoryVariantSummary(models.Model):
    _name = 'dl.wood.peeling.inventory.variant.summary'
    _description = 'Thống kê tồn kho ván bóc theo loại ván bóc'
    _order = 'qty_available desc, qty_initial desc'

    dossier_id = fields.Many2one('dl.wood.peeling.dossier', string='Hồ sơ', required=True, ondelete='cascade')
    variant_id = fields.Many2one('dl.wood.peeling.variant', string='Loại ván bóc')
    qty_initial = fields.Float(string='Tổng Khối lượng (m³)', digits=(16, 2))
    qty_used = fields.Float(string='Đã sử dụng (m³)', digits=(16, 2))
    qty_available = fields.Float(string='Tồn khả dụng (m³)', digits=(16, 2))

