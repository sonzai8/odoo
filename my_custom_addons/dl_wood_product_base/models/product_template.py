# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_is_wood_product = fields.Boolean(string='Là sản phẩm ngành gỗ', default=False)
    x_thickness_alias = fields.Char(string='Ký hiệu độ dày', help='Dùng để tra cứu bảng giá Ép Film (ví dụ: 11M, 14D...)')
    x_dimension_id = fields.Many2one('product.attribute.value', string='Khổ ván (Kích thước)', 
                                    domain=[('attribute_id.name', 'ilike', 'Kích thước')])
    
    x_quality = fields.Char(string='Hậu tố (Chất lượng)', size=4, help='Hậu tố để gắn vào sau mã và tên sản phẩm (VD: A, B, AB, FULL...)')

    # Kích thước
    x_thickness = fields.Float(string='Độ dày (mm)', digits=(16, 2))
    x_length = fields.Float(string='Chiều dài (mm)', digits=(16, 1), default=2440.0)
    x_width = fields.Float(string='Chiều rộng (mm)', digits=(16, 1), default=1220.0)
    x_area_m2 = fields.Float(string='Diện tích (m2)', compute='_compute_wood_measurements', store=True)
    x_volume_m3 = fields.Float(string='Khối lượng (m3)', compute='_compute_wood_measurements', store=True)

    # Cấu trúc lớp gỗ (Veneer)
    x_layer_a_count = fields.Integer(string='Số lớp A')
    x_layer_b_count = fields.Integer(string='Số lớp B')
    x_layer_c_count = fields.Integer(string='Số lớp C')
    
    x_structure_summary = fields.Char(string='Tóm tắt cấu trúc', compute='_compute_structure_summary', store=True)

    @api.depends('x_length', 'x_width', 'x_thickness')
    def _compute_wood_measurements(self):
        for product in self:
            area = (product.x_length * product.x_width) / 1000000.0
            product.x_area_m2 = area
            product.x_volume_m3 = (area * product.x_thickness) / 1000.0

    @api.depends('x_thickness', 'x_length', 'x_width', 'x_layer_a_count', 'x_layer_b_count', 'x_layer_c_count', 'x_quality')
    def _compute_structure_summary(self):
        for product in self:
            parts = []
            if product.x_thickness:
                parts.append(f"{product.x_thickness:g}mm")
            
            # Kích thước
            if product.x_length and product.x_width:
                parts.append(f"{int(product.x_length)}x{int(product.x_width)}")
            
            # Chất lượng (Hậu tố)
            if product.x_quality:
                parts.append(product.x_quality.upper())

            # Cấu trúc ván
            layers = []
            if product.x_layer_a_count: layers.append(f"{product.x_layer_a_count}A")
            if product.x_layer_b_count: layers.append(f"{product.x_layer_b_count}B")
            if product.x_layer_c_count: layers.append(f"{product.x_layer_c_count}C")
            if layers:
                parts.append("-".join(layers))
            
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

    x_unit = fields.Selection([
        ('sheet', 'Tấm'),
        ('m3', 'Mét khối (M3)'),
    ], string='Đơn vị tính (Gỗ)', default='sheet')

    x_sale_state = fields.Selection([
        ('active', 'Đang kinh doanh'),
        ('inactive', 'Ngừng kinh doanh'),
    ], string='Trạng thái kinh doanh', default='active')

    x_material_keo = fields.Boolean(string='Gỗ keo', compute='_compute_x_materials', store=True)
    x_material_thong = fields.Boolean(string='Gỗ thông', compute='_compute_x_materials', store=True)
    x_material_bach_dan = fields.Boolean(string='Gỗ bạch đàn', compute='_compute_x_materials', store=True)
    x_material_cao_su = fields.Boolean(string='Gỗ cao su', compute='_compute_x_materials', store=True)

    @api.depends('x_is_wood_product')
    def _compute_x_materials(self):
        for product in self:
            codes = []
            if hasattr(product, 'x_required_species_ids') and product.x_required_species_ids:
                codes = product.x_required_species_ids.mapped('code')
            product.x_material_keo = 'KEO' in codes
            product.x_material_thong = 'THONG' in codes
            product.x_material_bach_dan = 'BD' in codes
            product.x_material_cao_su = 'CS' in codes

    @api.onchange(
        'x_is_wood_product',
        'x_material_keo', 'x_material_thong', 'x_material_bach_dan', 'x_material_cao_su',
        'x_thickness', 'x_width', 'x_length',
        'list_price', 'x_unit', 'x_quality'
    )
    def _onchange_wood_name_and_code(self):
        for product in self:
            if not product.x_is_wood_product:
                continue
            
            # 1. Tự động sinh Tên sản phẩm
            materials = []
            if hasattr(product, 'x_required_species_ids') and product.x_required_species_ids:
                materials = [s.name.lower() for s in product.x_required_species_ids if s.name]
            materials_str = ", ".join(materials) if materials else ""
            
            thickness_str = f"{product.x_thickness:g}" if product.x_thickness else ""
            width_str = f"{int(product.x_width)}" if product.x_width else ""
            length_str = f"{int(product.x_length)}" if product.x_length else ""
            
            name_parts = []
            name_parts.append("Gỗ dán ( ván ép ) công nghiệp phủ phim")
            if materials_str:
                name_parts.append(f"sản xuất từ {materials_str}")
            
            if thickness_str or width_str or length_str:
                dim_parts = []
                dim_parts.append(f"{thickness_str}mm" if thickness_str else "")
                dim_parts.append(f"{width_str}mm" if width_str else "")
                dim_parts.append(f"{length_str}mm" if length_str else "")
                dim_parts = [p for p in dim_parts if p]
                dim_str = " x ".join(dim_parts)
                if product.x_quality:
                    name_parts.append(f"kích thước : {dim_str} {product.x_quality.upper()}")
                else:
                    name_parts.append(f"kích thước : {dim_str}")
            else:
                if product.x_quality:
                    name_parts.append(f"{product.x_quality.upper()}")
                
            product.name = " ".join(name_parts)
            
            wood_code = ""
            if hasattr(product, 'x_required_peeling_type_ids') and product.x_required_peeling_type_ids:
                codes = []
                for p in product.x_required_peeling_type_ids:
                    if p.code:
                        codes.append(p.code.upper())
                if codes:
                    codes.sort()
                    wood_code = "".join(codes)
            
            company = product.company_id or self.env.company
            prefix = getattr(company, 'x_wood_prefix', 'TPEP') or 'TPEP'
            seg1 = f"{prefix}{wood_code}"
            
            # Tự động thay đổi theo công thức: T = Tấm, M = m3
            unit_prefix = "M" if product.x_unit == "m3" else "T"
            seg2 = f"{unit_prefix}{product.x_thickness:.1f}" if product.x_thickness else ""
            
            seg3 = f"{int(product.list_price / 1000)}" if product.list_price else ""
            
            date = product.create_date or fields.Datetime.now()
            local_date = fields.Datetime.context_timestamp(product, date)
            seg4 = local_date.strftime("%m%y")
            
            code_parts = [seg1]
            if seg2: code_parts.append(seg2)
            if seg3: code_parts.append(seg3)
            if seg4: code_parts.append(seg4)
            
            if product.x_quality:
                product.x_quality = product.x_quality.upper()
                code_parts.append(product.x_quality)
            
            product.default_code = "_".join(code_parts)

    @api.constrains('default_code')
    def _check_unique_default_code(self):
        for product in self:
            if product.default_code:
                existing = self.env['product.template'].search([
                    ('default_code', '=', product.default_code),
                    ('id', '!=', product.id)
                ], limit=1)
                if existing:
                    raise ValidationError(f'Trùng mã! Mã sản phẩm ({product.default_code}) đã tồn tại trên Odoo. Vui lòng thay đổi "Hậu tố" hoặc Thông số để phân biệt.')

class ProductProduct(models.Model):
    _inherit = 'product.product'

    x_is_wood_product = fields.Boolean(related='product_tmpl_id.x_is_wood_product', readonly=True)
    x_thickness = fields.Float(related='product_tmpl_id.x_thickness', readonly=True)
    x_length = fields.Float(related='product_tmpl_id.x_length', readonly=True)
    x_width = fields.Float(related='product_tmpl_id.x_width', readonly=True)
    x_area_m2 = fields.Float(related='product_tmpl_id.x_area_m2', readonly=True)
    x_volume_m3 = fields.Float(related='product_tmpl_id.x_volume_m3', readonly=True)
    x_quality = fields.Char(related='product_tmpl_id.x_quality', readonly=True)
    x_unit = fields.Selection(related='product_tmpl_id.x_unit', readonly=True)
    x_sale_state = fields.Selection(related='product_tmpl_id.x_sale_state', readonly=True)
    x_material_keo = fields.Boolean(related='product_tmpl_id.x_material_keo', readonly=True)
    x_material_thong = fields.Boolean(related='product_tmpl_id.x_material_thong', readonly=True)
    x_material_bach_dan = fields.Boolean(related='product_tmpl_id.x_material_bach_dan', readonly=True)
    x_material_cao_su = fields.Boolean(related='product_tmpl_id.x_material_cao_su', readonly=True)
