# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DlWoodSpecies(models.Model):
    _name = 'dl.wood.species'
    _description = 'Loài gỗ'
    _inherit = ['dl.wood.log.mixin']

    name = fields.Char(string='Tên loài', required=True)
    name_en = fields.Char(string='Tên tiếng Anh')
    name_sci = fields.Char(string='Tên khoa học')
    material_name = fields.Char(string='Tên nguyên liệu')
    code = fields.Char(string='Mã loài')
    wood_type = fields.Selection([
        ('wood', 'Gỗ'),
        ('firewood', 'Củi')
    ], string='Phân loại', default='wood', required=True)
    x_species_group = fields.Selection([
        ('common', 'Thông thường'),
        ('precious', 'Danh mục loài nguy cấp, quý, hiếm'),
        ('cites', 'Phụ lục CITES')
    ], string='Nhóm loài', default='common', required=True)
    note = fields.Text(string='Ghi chú')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company)
    
    grade_ids = fields.One2many('dl.wood.species.grade', 'species_id', string='Phân loại')


class DlWoodSpeciesGrade(models.Model):
    _name = 'dl.wood.species.grade'
    _description = 'Phân loại chất lượng loài gỗ'

    species_id = fields.Many2one('dl.wood.species', string='Loài gỗ', ondelete='cascade')
    name = fields.Char(string='Tên phân loại', required=True)
    diameter_min = fields.Integer(string='Đường kính Min (cm)')
    diameter_max = fields.Integer(string='Đường kính Max (cm)')
    height = fields.Float(string='Chiều cao (m)')
    default_price = fields.Integer(string='Giá mặc định')
    note = fields.Char(string='Ghi chú')
    company_id = fields.Many2one('res.company', related='species_id.company_id', store=True, index=True)

    @api.depends('name', 'diameter_min', 'diameter_max', 'height')
    def _compute_display_name(self):
        for rec in self:
            # Format: Tên loại - (đường kính min - đường kính max) - chiều cao
            # Ví dụ: Loại A - (14-16) - 2,6
            diameter_str = f"({rec.diameter_min}-{rec.diameter_max})" if rec.diameter_min or rec.diameter_max else ""
            height_str = f"{rec.height:.1f}".replace('.', ',') if rec.height else ""
            
            parts = [rec.name]
            if diameter_str: parts.append(diameter_str)
            if height_str: parts.append(height_str)
            
            rec.display_name = " - ".join(parts)
