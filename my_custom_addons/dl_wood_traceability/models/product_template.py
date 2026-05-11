# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_wood_product = fields.Boolean(
        string='Là sản phẩm Gỗ', 
        help='Nếu chọn, sản phẩm sẽ bắt buộc quản lý theo Lô (Lot).',
        default=False
    )
    x_woodpro_id = fields.Char(string='ID WoodPro', index=True)

    @api.onchange('is_wood_product')
    def _onchange_is_wood_product(self):
        """Tự động thiết lập quản lý theo Lô khi tích chọn là sản phẩm Gỗ"""
        if self.is_wood_product:
            self.tracking = 'lot'
