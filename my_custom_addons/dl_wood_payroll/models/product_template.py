# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_is_film_product = fields.Boolean(string='Là sản phẩm Ép Film', default=False, help='Đánh dấu sản phẩm có công đoạn ép phim để cấu hình đơn giá.')
    x_is_support_product = fields.Boolean(string='Là sản phẩm hỗ trợ', default=False, help='Sản phẩm tính lương cho chuyền nhưng không tính vào báo cáo sản lượng chính.')

class ProductProduct(models.Model):
    _inherit = 'product.product'

    x_is_film_product = fields.Boolean(related='product_tmpl_id.x_is_film_product', readonly=True)
    x_is_support_product = fields.Boolean(related='product_tmpl_id.x_is_support_product', readonly=True)
