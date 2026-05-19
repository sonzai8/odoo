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

    def action_init_vietnam_banks(self):
        """Khởi tạo danh sách các ngân hàng phổ biến nhất Việt Nam"""
        bank_obj = self.env['dl.vietnam.bank']
        
        # Danh sách ngân hàng sắp xếp theo mức độ phổ biến giảm dần (sequence tăng dần)
        data = [
            ('Ngân hàng TMCP Quân đội', 'MB Bank', 'MBB', 10),
            ('Ngân hàng TMCP Ngoại thương Việt Nam', 'Vietcombank', 'VCB', 20),
            ('Ngân hàng TMCP Đầu tư và Phát triển Việt Nam', 'BIDV', 'BIDV', 30),
            ('Ngân hàng Nông nghiệp và Phát triển Nông thôn Việt Nam', 'Agribank', 'VBA', 40),
            ('Ngân hàng TMCP Công thương Việt Nam', 'VietinBank', 'CTG', 50),
            ('Ngân hàng TMCP Kỹ thương Việt Nam', 'Techcombank', 'TCB', 60),
            ('Ngân hàng TMCP Sài Gòn Thương Tín', 'Sacombank', 'STB', 70),
            ('Ngân hàng TMCP Á Châu', 'ACB', 'ACB', 80),
            ('Ngân hàng TMCP Việt Nam Thịnh Vượng', 'VPBank', 'VPB', 90),
            ('Ngân hàng TMCP Tiên Phong', 'TPBank', 'TPB', 100),
            ('Ngân hàng TMCP Phát triển Thành phố Hồ Chí Minh', 'HDBank', 'HDB', 110),
            ('Ngân hàng TMCP Sài Gòn - Hà Nội', 'SHB', 'SHB', 120),
            ('Ngân hàng TMCP Quốc tế Việt Nam', 'VIB', 'VIB', 130),
            ('Ngân hàng TMCP Hàng Hải Việt Nam', 'MSB', 'MSB', 140),
            ('Ngân hàng TMCP Lộc Phát Việt Nam', 'LPBank', 'LPB', 150),
            ('Ngân hàng TMCP Đông Nam Á', 'SeABank', 'SSB', 160),
            ('Ngân hàng TMCP Phương Đông', 'OCB', 'OCB', 170),
            ('Ngân hàng TMCP Xuất Nhập khẩu Việt Nam', 'Eximbank', 'EIB', 180),
            ('Ngân hàng TMCP Bắc Á', 'Bac A Bank', 'BAB', 190),
            ('Ngân hàng TMCP Đại Chúng Việt Nam', 'PVcomBank', 'PVB', 200),
        ]
        
        for name, short_name, code, sequence in data:
            existing = bank_obj.search([('short_name', '=', short_name), ('company_id', '=', self.env.company.id)], limit=1)
            if not existing:
                bank_obj.create({
                    'name': name,
                    'short_name': short_name,
                    'code': code,
                    'sequence': sequence,
                    'company_id': self.env.company.id
                })
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành công'),
                'message': _('Đã khởi tạo danh mục ngân hàng Việt Nam thành công.'),
                'sticky': False,
                'type': 'success',
            }
        }
