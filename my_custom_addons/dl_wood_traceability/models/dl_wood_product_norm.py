# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DlWoodProductNorm(models.Model):
    _name = 'dl.wood.product.norm'
    _description = 'Định mức nguyên liệu gỗ'

    product_tmpl_id = fields.Many2one(
        'product.template', 
        string='Sản phẩm', 
        ondelete='cascade', 
        required=True
    )
    species_id = fields.Many2one(
        'dl.wood.species', 
        string='Loại gỗ nguyên liệu', 
        required=True
    )
    norm_quantity = fields.Float(
        string='Định mức (m3)', 
        digits=(16, 2), 
        required=True,
        help='Số lượng m3 gỗ nguyên liệu cần để sản xuất 1 đơn vị thành phẩm (m2 hoặc tấm)'
    )
    note = fields.Char(string='Ghi chú')
