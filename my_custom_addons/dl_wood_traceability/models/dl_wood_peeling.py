# -*- coding: utf-8 -*-
"""
Quản lý Hồ Sơ Ván Bóc — Nguồn nguyên liệu thứ hai bên cạnh gỗ tự nhiên.
Ván bóc là thành phẩm sau khi thu hoạch gỗ, được mua từ các NCC chuyên biệt (Công ty).
"""
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  DANH MỤC VÁN BÓC (Master Data)                                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class DlWoodPeelingType(models.Model):
    """Danh mục các loại ván bóc mà công ty thu mua."""
    _name = 'dl.wood.peeling.type'
    _description = 'Danh mục Ván Bóc'
    _order = 'sequence, name'

    name = fields.Char(string='Tên loại ván bóc', required=True, index=True)
    name_en = fields.Char(string='Tên tiếng Anh')
    name_sci = fields.Char(string='Tên khoa học')
    code = fields.Char(string='Mã viết tắt', index=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    note = fields.Text(string='Ghi chú')
    active = fields.Boolean(string='Hoạt động', default=True)
    company_id = fields.Many2one(
        'res.company', string='Công ty',
        default=lambda self: self.env.company
    )

    _name_unique = models.Constraint(
        'unique(name, company_id)',
        'Tên loại ván bóc đã tồn tại trong công ty này!'
    )


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  HỒ SƠ VÁN BÓC (Lô hàng mua từ NCC)                                     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class DlWoodPeelingDossier(models.Model):
    """Hồ sơ ván bóc — quản lý từng lô hàng mua từ NCC ván bóc."""
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
        """Tự động sinh mã hồ sơ: PB_HS_0001, PB_HS_0002..."""
        prefix = self.env.company.x_wood_prefix or "XX"
        count = self.search_count([('company_id', '=', self.env.company.id)])
        return f"{prefix}_PB_{(count + 1):04d}"

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

    # ── Trạng thái ────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('using', 'Đang dùng'),
        ('done', 'Hết'),
    ], string='Trạng thái', default='draft', index=True, tracking=True)

    # ── Dòng chi tiết ─────────────────────────────────────────────────────────
    line_ids = fields.One2many(
        'dl.wood.peeling.dossier.line', 'dossier_id',
        string='Chi tiết ván bóc'
    )

    # ── Tổng hợp khối lượng (compute) ────────────────────────────────────────
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

    @api.depends('line_ids.qty_initial', 'line_ids.qty_used', 'line_ids.qty_available',
                 'line_ids.x_subtotal')
    def _compute_qty_totals(self):
        for rec in self:
            rec.qty_initial = sum(rec.line_ids.mapped('qty_initial'))
            rec.qty_used = sum(rec.line_ids.mapped('qty_used'))
            rec.qty_available = sum(rec.line_ids.mapped('qty_available'))
            rec.x_total_cost = sum(rec.line_ids.mapped('x_subtotal'))

    # ── Tài liệu PDF (5 nhóm) ────────────────────────────────────────────────
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
    x_invoice_attachment_ids = fields.Many2many(
        'ir.attachment',
        'dl_peeling_dossier_invoice_attachment_rel',
        'dossier_id', 'attachment_id',
        string='Hóa đơn / Phiếu thu'
    )
    x_transport_attachment_ids = fields.Many2many(
        'ir.attachment',
        'dl_peeling_dossier_transport_attachment_rel',
        'dossier_id', 'attachment_id',
        string='Chứng từ vận chuyển'
    )
    x_quality_attachment_ids = fields.Many2many(
        'ir.attachment',
        'dl_peeling_dossier_quality_attachment_rel',
        'dossier_id', 'attachment_id',
        string='Kiểm định chất lượng'
    )

    # ── Actions chuyển trạng thái ─────────────────────────────────────────────
    def action_confirm(self):
        """Chuyển sang trạng thái 'Đang dùng'."""
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('Vui lòng thêm ít nhất 1 dòng chi tiết ván bóc trước khi xác nhận.'))
            rec.state = 'using'

    def action_done(self):
        """Chuyển sang trạng thái 'Hết'."""
        for rec in self:
            rec.state = 'done'

    def action_draft(self):
        """Quay về trạng thái 'Dự thảo'."""
        for rec in self:
            rec.state = 'draft'

    # ── Khởi tạo dữ liệu mẫu ────────────────────────────────────────────────
    @api.model
    def action_init_peeling_types(self):
        """Khởi tạo 4 loại ván bóc mặc định."""
        PeelingType = self.env['dl.wood.peeling.type']
        default_types = [
            {'name': 'Ván bóc gỗ bạch đàn', 'code': 'VB_BD', 'sequence': 10},
            {'name': 'Ván bóc gỗ cao su', 'code': 'VB_CS', 'sequence': 20},
            {'name': 'Ván bóc gỗ keo', 'code': 'VB_KEO', 'sequence': 30},
            {'name': 'Ván bóc gỗ thông', 'code': 'VB_TH', 'sequence': 40},
        ]
        created_count = 0
        for dt in default_types:
            existing = PeelingType.search([
                ('name', '=', dt['name']),
                ('company_id', '=', self.env.company.id)
            ], limit=1)
            if not existing:
                PeelingType.create({
                    **dt,
                    'company_id': self.env.company.id,
                })
                created_count += 1

        if created_count > 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Thành công'),
                    'message': _('Đã khởi tạo %d loại ván bóc mặc định.') % created_count,
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                },
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Thông tin'),
                    'message': _('Tất cả các loại ván bóc mặc định đã tồn tại.'),
                    'type': 'info',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                },
            }


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  DÒNG CHI TIẾT VÁN BÓC (Từng loại ván bóc trong 1 hồ sơ)                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class DlWoodPeelingDossierLine(models.Model):
    """Chi tiết từng loại ván bóc trong hồ sơ — theo dõi tồn kho trừ lùi."""
    _name = 'dl.wood.peeling.dossier.line'
    _description = 'Chi tiết Ván Bóc trong Hồ Sơ'
    _order = 'peeling_type_id'

    dossier_id = fields.Many2one(
        'dl.wood.peeling.dossier', string='Hồ sơ ván bóc',
        ondelete='cascade', required=True, index=True
    )
    peeling_type_id = fields.Many2one(
        'dl.wood.peeling.type', string='Loại ván bóc',
        required=True, index=True
    )
    qty_initial = fields.Float(
        string='KL ban đầu (m³)', digits=(16, 2), required=True,
        help='Khối lượng ván bóc ban đầu theo hồ sơ mua.'
    )
    qty_used = fields.Float(
        string='KL đã dùng (m³)', digits=(16, 2), default=0.0,
        help='Khối lượng đã tiêu hao trong các Lệnh sản xuất (cộng dồn khi trừ lùi).'
    )
    qty_available = fields.Float(
        string='Tồn khả dụng (m³)',
        compute='_compute_qty_available', store=True, digits=(16, 2)
    )
    price_unit = fields.Float(
        string='Đơn giá (VND/m³)', digits=(16, 2),
        help='Đơn giá mua ván bóc'
    )
    x_subtotal = fields.Float(
        string='Thành tiền (VND)',
        compute='_compute_x_subtotal', store=True, digits=(16, 2)
    )

    @api.depends('qty_initial', 'qty_used')
    def _compute_qty_available(self):
        for line in self:
            line.qty_available = max(0.0, line.qty_initial - line.qty_used)

    @api.depends('qty_initial', 'price_unit')
    def _compute_x_subtotal(self):
        for line in self:
            line.x_subtotal = round(line.qty_initial * line.price_unit, 2)
