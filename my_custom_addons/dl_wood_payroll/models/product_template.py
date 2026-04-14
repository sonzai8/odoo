# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_is_wood_product = fields.Boolean(string='Là sản phẩm ngành gỗ', default=False)
    x_thickness = fields.Float(string='Độ dày (mm)', digits=(16, 2))
    x_length = fields.Float(string='Chiều dài (cm)', digits=(16, 1))
    x_width = fields.Float(string='Chiều rộng (cm)', digits=(16, 1))
    
    x_dimension_id = fields.Many2one('product.attribute.value', string='Khổ ván (Kích thước)', 
                                    domain=[('attribute_id.name', 'ilike', 'Kích thước')])
    
    x_coating_type = fields.Selection([
        ('none', 'Không phủ film'),
        ('1_side', 'Phủ 1 mặt'),
        ('2_side', 'Phủ 2 mặt')
    ], string='Hình thức phủ', default='none')
    
    x_film_id = fields.Many2one('dl.film.type', string='Loại Film')
    
    # Cấu trúc lớp gỗ (Veneer)
    x_layer_a_count = fields.Integer(string='Số lớp A')
    x_layer_b_count = fields.Integer(string='Số lớp B')
    x_layer_c_count = fields.Integer(string='Số lớp C')
    
    x_structure_summary = fields.Char(string='Tóm tắt cấu trúc', compute='_compute_structure_summary', store=True)

    # Quy đổi đơn vị
    x_area_m2 = fields.Float(string='Diện tích (m2)', compute='_compute_wood_measurements', store=True)
    x_volume_m3 = fields.Float(string='Khối lượng (m3)', compute='_compute_wood_measurements', store=True)

    @api.depends('x_length', 'x_width', 'x_thickness')
    def _compute_wood_measurements(self):
        for product in self:
            area = (product.x_length * product.x_width) / 10000.0
            product.x_area_m2 = area
            product.x_volume_m3 = (area * product.x_thickness) / 1000.0

    @api.depends('x_thickness', 'x_length', 'x_width', 'x_layer_a_count', 'x_layer_b_count', 'x_layer_c_count', 'x_film_id', 'x_coating_type')
    def _compute_structure_summary(self):
        for product in self:
            parts = []
            if product.x_thickness:
                parts.append(f"{product.x_thickness:g}mm")
            
            # Kích thước
            if product.x_length and product.x_width:
                parts.append(f"{int(product.x_length)}x{int(product.x_width)}")
            
            # Cấu trúc ván
            layers = []
            if product.x_layer_a_count: layers.append(f"{product.x_layer_a_count}A")
            if product.x_layer_b_count: layers.append(f"{product.x_layer_b_count}B")
            if product.x_layer_c_count: layers.append(f"{product.x_layer_c_count}C")
            if layers:
                parts.append("-".join(layers))
            
            # Film & Phủ
            if product.x_coating_type != 'none':
                film_name = product.x_film_id.name or 'N/A'
                side_text = "1 mặt" if product.x_coating_type == '1_side' else "2 mặt"
                parts.append(f"Film {film_name} ({side_text})")
            
            product.x_structure_summary = " | ".join(parts)

    def _compute_display_name(self):
        super()._compute_display_name()
        for product in self:
            if product.x_is_wood_product:
                spec = product.x_structure_summary
                if spec:
                    product.display_name = f"{product.name} [{spec}]"

    @api.constrains('x_is_wood_product', 'x_length', 'x_width', 'x_thickness')
    def _check_wood_specs(self):
        for product in self:
            if product.x_is_wood_product:
                if product.x_length <= 0 or product.x_width <= 0 or product.x_thickness <= 0:
                    raise ValidationError("Kích thước và Độ dày sản phẩm gỗ phải lớn hơn 0!")
