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


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _compute_display_name(self):
        super()._compute_display_name()
        for product in self:
            is_wood = product.product_tmpl_id.is_wood_product or getattr(product, 'x_is_wood_product', False)
            if is_wood and product.default_code:
                code = product.default_code.strip()
                if code:
                    name = product.name or ''
                    spec = getattr(product.product_tmpl_id, 'x_structure_summary', False)
                    # Định dạng: [Mã] Tên [Thông số kỹ thuật]
                    if spec:
                        product.display_name = f"[{code}] {name} [{spec}]"
                    else:
                        product.display_name = f"[{code}] {name}"
