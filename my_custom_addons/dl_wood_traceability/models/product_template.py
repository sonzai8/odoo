# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_wood_product = fields.Boolean(
        string='Là thành phẩm', 
        help='Nếu chọn, sản phẩm sẽ bắt buộc quản lý theo Lô (Lot).',
        default=False
    )
    x_woodpro_id = fields.Char(string='ID WoodPro', index=True)
    x_thickness = fields.Float(string='Độ dày (mm)')
    x_width = fields.Float(string='Chiều rộng (mm)')
    x_length = fields.Float(string='Chiều dài (mm)')
    
    x_norm_ids = fields.One2many(
        'dl.wood.product.norm', 
        'product_tmpl_id', 
        string='Định mức nguyên liệu'
    )

    @api.onchange('is_wood_product')
    def _onchange_is_wood_product(self):
        """Tự động thiết lập quản lý theo Lô khi tích chọn là thành phẩm"""
        if self.is_wood_product:
            self.tracking = 'lot'
