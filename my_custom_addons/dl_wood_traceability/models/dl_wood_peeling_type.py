# -*- coding: utf-8 -*-
"""
Master data: Loại Ván Bóc.
Ván bóc là thành phẩm chế biến từ 1 loại gỗ nhất định.
Ví dụ: Ván bóc Keo (từ Gỗ keo), Ván bóc Thông (từ Gỗ thông).
"""
from odoo import models, fields, api


class DlWoodPeelingType(models.Model):
    """Danh mục Loại Ván Bóc — Master data được chọn khi nhập hoá đơn/lệnh sản xuất."""
    _name = 'dl.wood.peeling.type'
    _description = 'Loại Ván Bóc'
    _order = 'sequence asc, name asc'

    # ── Display name ──────────────────────────────────────────────────────────
    @api.depends('name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name or '???'

    # ── Thông tin cơ bản ──────────────────────────────────────────────────────
    name = fields.Char(
        string='Tên loại ván bóc', required=True,
        help='Ví dụ: Ván bóc Keo, Ván bóc Thông'
    )
    code = fields.Char(
        string='Mã', index=True,
        help='Mã ngắn để sinh mã/lọc nhanh (VD: VB_KEO_17)'
    )
    variant_ids = fields.One2many(
        'dl.wood.peeling.variant', 'peeling_type_id', string='Các biến thể'
    )
    species_id = fields.Many2one(
        'dl.wood.species', string='Loài gỗ nguồn',
        help='Loài gỗ được dùng để sản xuất ra loại ván bóc này',
        ondelete='set null'
    )
    name_en = fields.Char(string='Tên tiếng Anh', related='species_id.name_en', readonly=True, store=True)
    name_sci = fields.Char(string='Tên khoa học', related='species_id.name_sci', readonly=True, store=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    note = fields.Text(string='Ghi chú')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Công ty',
        required=True, default=lambda self: self.env.company, index=True
    )

class DlWoodPeelingVariant(models.Model):
    """Danh mục Biến thể Ván Bóc — Master data được chọn khi nhập hoá đơn/lệnh sản xuất."""
    _name = 'dl.wood.peeling.variant'
    _description = 'Biến thể Ván Bóc'
    _order = 'peeling_type_id asc, thickness asc'

    name = fields.Char(string='Tên biến thể', compute='_compute_name', store=True)
    peeling_type_id = fields.Many2one(
        'dl.wood.peeling.type', string='Loại ván bóc',
        required=True, ondelete='cascade'
    )
    thickness = fields.Selection([
        ('1.7', '1,7 ly'),
        ('2.0', '2,0 ly')
    ], string='Độ dày', required=True)
    length = fields.Float(string='Chiều dài (mm)', default=1270.0, required=True)
    width = fields.Float(string='Chiều rộng (mm)', default=640.0, required=True)
    active = fields.Boolean(default=True)
    
    @api.depends('peeling_type_id.name', 'thickness')
    def _compute_name(self):
        for rec in self:
            if rec.peeling_type_id and rec.thickness:
                rec.name = f"{rec.peeling_type_id.name} {rec.thickness} ly"
            elif rec.peeling_type_id:
                rec.name = rec.peeling_type_id.name
            else:
                rec.name = "Chưa xác định"
