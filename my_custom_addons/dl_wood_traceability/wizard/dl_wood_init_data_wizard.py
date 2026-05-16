# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class DlWoodInitDataWizard(models.TransientModel):
    _name = 'dl.wood.init.data.wizard'
    _description = 'Khởi Tạo Dữ Liệu Gỗ'

    def action_init_wood_species(self):
        """Khởi tạo danh sách loài gỗ mặc định"""
        species_obj = self.env['dl.wood.species']
        
        data = [
            ('Gỗ keo', 'Acacia wood', 'Acacia mangium', 'wood', 'KEO'),
            ('Gỗ thông mã vĩ', 'Horsetail pine wood', 'Pinus massoniana', 'wood', 'TMV'),
            ('Gỗ bạch đàn', 'Eucalyptus wood', 'Eucalyptus', 'wood', 'BD'),
            ('Gỗ thông', 'Pine wood', 'Pinus', 'wood', 'THONG'),
            ('Keo lai', 'Hybrid acacia', 'Acacia hybrid', 'wood', 'KL'),
            ('Củi keo', 'Acacia firewood', 'Acacia mangium', 'firewood', 'CUI_KEO'),
            ('Củi bạch đàn', 'Eucalyptus firewood', 'Eucalyptus', 'firewood', 'CUI_BD'),
            ('Gỗ cao su', 'Rubberwood', 'Hevea brasiliensis', 'wood', 'CS'),
            ('Gỗ keo tròn', 'Acacia logs', 'Acacia mangium', 'wood', 'KEO_TRON'),
            ('Acacia', 'Acacia', 'Acacia', 'wood', 'ACACIA'),
            ('Pine Wood', 'Pine wood', 'Pinus', 'wood', 'PINE'),
            ('Eucalyptus', 'Eucalyptus', 'Eucalyptus', 'wood', 'EUCALYPTUS'),
        ]
        
        for name, name_en, name_sci, wood_type, code in data:
            existing = species_obj.search([('name', '=', name), ('company_id', '=', self.env.company.id)], limit=1)
            if not existing:
                species_obj.create({
                    'name': name,
                    'name_en': name_en,
                    'name_sci': name_sci,
                    'wood_type': wood_type,
                    'code': code,
                    'company_id': self.env.company.id
                })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành công'),
                'message': _('Đã khởi tạo danh mục loài gỗ cho công ty hiện tại.'),
                'sticky': False,
                'type': 'success',
            }
        }
