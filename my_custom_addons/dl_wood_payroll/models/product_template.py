# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Trường dùng để đánh dấu/lọc các thuộc tính sản xuất cụ thể nếu cần
    # Mặc định Odoo đã quản lý Product Attributes rất tốt.
    # User muốn tab "Thuộc tính sản xuất" trên form.
    
    x_is_wood_product = fields.Boolean(string='Là sản phẩm ngành gỗ', default=True)
