# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_is_wood_product = fields.Boolean(string='Là sản phẩm ngành gỗ', default=False)
    is_wood_product = fields.Boolean(string='Là sản phẩm Gỗ', default=False)
    x_is_film_product = fields.Boolean(string='Là sản phẩm Ép Film', default=False, help='Đánh dấu sản phẩm có công đoạn ép phim để cấu hình đơn giá.')
    x_is_support_product = fields.Boolean(string='Là sản phẩm hỗ trợ', default=False, help='Sản phẩm tính lương cho chuyền nhưng không tính vào báo cáo sản lượng chính.')
    x_thickness = fields.Float(string='Độ dày (mm)', digits=(16, 2))
    x_thickness_alias = fields.Char(string='Ký hiệu độ dày', help='Dùng để tra cứu bảng giá Ép Film (ví dụ: 11M, 14D...)')
    x_length = fields.Float(string='Chiều dài (mm)', digits=(16, 1))
    x_width = fields.Float(string='Chiều rộng (mm)', digits=(16, 1))
    
    x_dimension_id = fields.Many2one('product.attribute.value', string='Khổ ván (Kích thước)', 
                                    domain=[('attribute_id.name', 'ilike', 'Kích thước')])
    
    
    x_quality = fields.Selection([
        ('a', 'Loại A'),
        ('b', 'Loại B'),
        ('c', 'Loại C'),
        ('ab', 'Loại A/B'),
        ('bc', 'Loại B/C'),
        ('full_a', 'Full A'),
    ], string='Chất lượng ván', default='a')

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
            # Quy đổi từ mm2 sang m2: chia cho 1,000,000.0
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
            
            # Chất lượng
            if product.x_quality:
                quality_map = dict(self._fields['x_quality'].selection)
                parts.append(quality_map.get(product.x_quality, product.x_quality).replace('Loại ', ''))

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

    x_material_keo = fields.Boolean(string='Gỗ keo', default=False)
    x_material_thong = fields.Boolean(string='Gỗ thông', default=False)
    x_material_bach_dan = fields.Boolean(string='Gỗ bạch đàn', default=False)
    x_material_cao_su = fields.Boolean(string='Gỗ cao su', default=False)

    @api.onchange(
        'x_is_wood_product',
        'x_material_keo', 'x_material_thong', 'x_material_bach_dan', 'x_material_cao_su',
        'x_thickness', 'x_width', 'x_length',
        'list_price'
    )
    def _onchange_wood_name_and_code(self):
        for product in self:
            if not product.x_is_wood_product:
                continue
            
            # 1. Tự động sinh Tên sản phẩm
            materials = []
            if product.x_material_keo: materials.append("Gỗ keo")
            if product.x_material_thong: materials.append("Gỗ thông")
            if product.x_material_bach_dan: materials.append("Gỗ bạch đàn")
            if product.x_material_cao_su: materials.append("Gỗ cao su")
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
                dim_parts.append(f"{thickness_str} mm" if thickness_str else "")
                dim_parts.append(f"{width_str}mm" if width_str else "")
                dim_parts.append(f"{length_str}mm" if length_str else "")
                dim_parts = [p for p in dim_parts if p]
                dim_str = " x ".join(dim_parts)
                name_parts.append(f"kích thước : {dim_str} .")
            else:
                name_parts.append(".")
                
            product.name = " ".join(name_parts)
            
            # 2. Tự động sinh Mã tham chiếu (default_code)
            wood_codes = []
            if product.x_material_keo: wood_codes.append("K")
            if product.x_material_thong: wood_codes.append("TH")
            if product.x_material_bach_dan: wood_codes.append("BD")
            if product.x_material_cao_su: wood_codes.append("CS")
            wood_code = "".join(wood_codes)
            
            company = product.company_id or self.env.company
            prefix = getattr(company, 'x_wood_prefix', 'TPEP') or 'TPEP'
            seg1 = f"{prefix}{wood_code}"
            
            seg2 = f"M{product.x_thickness:.1f}" if product.x_thickness else ""
            
            seg3 = f"{int(product.list_price / 1000)}" if product.list_price else ""
            
            date = product.create_date or fields.Datetime.now()
            seg4 = date.strftime("%m_%y")
            
            code_parts = [seg1]
            if seg2: code_parts.append(seg2)
            if seg3: code_parts.append(seg3)
            if seg4: code_parts.append(seg4)
            
            product.default_code = "_".join(code_parts)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    x_is_wood_product = fields.Boolean(related='product_tmpl_id.x_is_wood_product', readonly=True)
    x_is_film_product = fields.Boolean(related='product_tmpl_id.x_is_film_product', readonly=True)
    x_is_support_product = fields.Boolean(related='product_tmpl_id.x_is_support_product', readonly=True)
    x_thickness = fields.Float(related='product_tmpl_id.x_thickness', readonly=True)
    x_length = fields.Float(related='product_tmpl_id.x_length', readonly=True)
    x_width = fields.Float(related='product_tmpl_id.x_width', readonly=True)
    x_quality = fields.Selection(related='product_tmpl_id.x_quality', readonly=True)
    x_unit = fields.Selection(related='product_tmpl_id.x_unit', readonly=True)
    x_sale_state = fields.Selection(related='product_tmpl_id.x_sale_state', readonly=True)
    x_material_keo = fields.Boolean(related='product_tmpl_id.x_material_keo', readonly=True)
    x_material_thong = fields.Boolean(related='product_tmpl_id.x_material_thong', readonly=True)
    x_material_bach_dan = fields.Boolean(related='product_tmpl_id.x_material_bach_dan', readonly=True)
    x_material_cao_su = fields.Boolean(related='product_tmpl_id.x_material_cao_su', readonly=True)
    is_wood_product = fields.Boolean(related='product_tmpl_id.is_wood_product', readonly=True)
