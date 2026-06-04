# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DlWoodSpecies(models.Model):
    _name = 'dl.wood.species'
    _description = 'Loài gỗ'
    _inherit = ['dl.wood.log.mixin']
    _order = 'wood_type desc, name asc'

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
    uom_id = fields.Many2one(
        'uom.uom', 
        string='Đơn vị tính', 
        compute='_compute_uom_id', 
        store=True, 
        readonly=False,
        help='Đơn vị tính mặc định: Gỗ là m³, Củi là Ster.'
    )

    @api.depends('wood_type')
    def _compute_uom_id(self):
        for rec in self:
            if rec.wood_type == 'wood':
                uom = self.env['uom.uom'].search([('name', 'in', ('m³', 'Mét khối', 'Mét khối M3'))], limit=1)
                rec.uom_id = uom.id if uom else False
            elif rec.wood_type == 'firewood':
                uom = self.env['uom.uom'].search([('name', 'in', ('Ster', 'ster', 'ST', 'Ster/Củi'))], limit=1)
                if not uom:
                    # Tìm đơn vị gốc là m3
                    ref_uom = self.env['uom.uom'].search([('name', 'in', ('m³', 'Mét khối', 'Mét khối M3'))], limit=1)
                    uom_vals = {
                        'name': 'Ster',
                        'relative_factor': 1.0,
                    }
                    if ref_uom:
                        uom_vals['relative_uom_id'] = ref_uom.id
                    uom = self.env['uom.uom'].create(uom_vals)
                rec.uom_id = uom.id if uom else False
            else:
                rec.uom_id = False
    def action_init_peeling_types(self):
        """Khởi tạo danh mục ván bóc từ các loài gỗ hiện tại (Bỏ qua Củi, tự động tạo 1.7 ly và 2.0 ly)"""
        PeelingType = self.env['dl.wood.peeling.type']
        PeelingVariant = self.env['dl.wood.peeling.variant']
        created_count = 0
        thickness_variants = [
            ('1.7', '1,7 ly'),
            ('2.0', '2,0 ly')
        ]
        
        for species in self.filtered(lambda s: s.wood_type == 'wood'):
            # Check if peeling type already exists for this species
            ptype = PeelingType.search([
                ('species_id', '=', species.id)
            ], limit=1)
            
            if not ptype:
                # Determine code based on species name
                code = ''
                lower_name = species.name.lower()
                if 'keo' in lower_name: code = 'K'
                elif 'bạch đàn' in lower_name: code = 'BD'
                elif 'thông' in lower_name: code = 'T'
                elif 'cao su' in lower_name: code = 'CS'
                
                ptype = PeelingType.create({
                    'name': f"Ván bóc {species.name.lower()}",
                    'code': code or species.code,
                    'species_id': species.id,
                    'company_id': species.company_id.id or self.env.company.id,
                })
                created_count += 1
            
            for thickness_val, thickness_label in thickness_variants:
                # Check if variant exists
                existing_variant = PeelingVariant.search([
                    ('peeling_type_id', '=', ptype.id),
                    ('thickness', '=', thickness_val)
                ], limit=1)
                
                if not existing_variant:
                    PeelingVariant.create({
                        'peeling_type_id': ptype.id,
                        'thickness': thickness_val,
                        'length': 1270.0,
                        'width': 640.0,
                    })
                    
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Khởi tạo thành công',
                'message': f'Đã khởi tạo {created_count} Loại Ván Bóc mới từ danh mục gỗ.',
                'sticky': False,
                'type': 'success',
            }
        }


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
