# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class DlWoodInitDataWizard(models.TransientModel):
    _name = 'dl.wood.init.data.wizard'
    _description = 'Khởi Tạo Dữ Liệu Gỗ'

    def action_init_wood_species(self):
        """Khởi tạo danh sách loài gỗ và phân loại chi tiết"""
        species_obj = self.env['dl.wood.species']
        grade_obj = self.env['dl.wood.species.grade']
        
        data = [
            # Tên loài, Tên tiếng Anh, Tên khoa học, wood_type, code, Đường kính Min, Đường kính Max, Chiều dài, Giá (VNĐ), Ghi chú/Tên phân loại
            ('Gỗ keo', 'Acacia wood', 'Acacia', 'wood', 'KEO', 7, 10, 2.6, 1820000, 'Keo nhỏ'),
            ('Gỗ keo', 'Acacia wood', 'Acacia', 'wood', 'KEO', 10, 14, 2.6, 2150000, 'Keo trung'),
            ('Gỗ keo', 'Acacia wood', 'Acacia', 'wood', 'KEO', 14, 17, 2.6, 1700000, 'Keo lớn'),
            ('Gỗ keo', 'Acacia wood', 'Acacia', 'wood', 'KEO', 6, 22, 2.6, 1900000, 'Keo xô (Dải rộng)'),
            ('Gỗ keo', 'Acacia wood', 'Acacia', 'wood', 'KEO', 17, 30, 1.3, 2300000, 'Keo to cắt ngắn (1.3m)'),
            
            ('Gỗ thông', 'Pine wood', 'Pinus massoniana', 'wood', 'THONG', 8, 14, 2.6, 1800000, 'Thông nhỏ'),
            ('Gỗ thông', 'Pine wood', 'Pinus massoniana', 'wood', 'THONG', 14, 20, 2.6, 2100000, 'Thông trung'),
            ('Gỗ thông', 'Pine wood', 'Pinus massoniana', 'wood', 'THONG', 12, 32, 2.6, 1800000, 'Thông xô / Thông lớn'),
            ('Gỗ thông', 'Pine wood', 'Pinus massoniana', 'wood', 'THONG', 10, 20, 1.3, 1700000, 'Thông cắt ngắn (1.3m)'),
            
            ('Gỗ bạch đàn', 'Eucalyptus wood', 'Eucalyptus', 'wood', 'BD', 7, 12, 2.6, 1900000, 'Bạch đàn nhỏ'),
            ('Gỗ bạch đàn', 'Eucalyptus wood', 'Eucalyptus', 'wood', 'BD', 12, 16, 2.6, 2350000, 'Bạch đàn trung'),
            ('Gỗ bạch đàn', 'Eucalyptus wood', 'Eucalyptus', 'wood', 'BD', 16, 20, 2.6, 1900000, 'Bạch đàn lớn'),
            ('Gỗ bạch đàn', 'Eucalyptus wood', 'Eucalyptus', 'wood', 'BD', 6, 18, 2.6, 2100000, 'Bạch đàn xô (Dải rộng)'),
            
            ('Gỗ cao su', 'Rubberwood', 'Hevea brasiliensis', 'wood', 'CS', 14, 20, 2.6, 1820000, 'Gỗ cao su'),
            
            ('Củi thông', 'Pine firewood', 'Pinus massoniana', 'firewood', 'CUI_THONG', 0, 0, 0.0, 850000, 'Mặc định'),
            ('Củi keo', 'Acacia firewood', 'Acacia', 'firewood', 'CUI_KEO', 0, 0, 0.0, 850000, 'Mặc định'),
            ('Củi bạch đàn', 'Eucalyptus firewood', 'Eucalyptus', 'firewood', 'CUI_BD', 0, 0, 0.0, 900000, 'Mặc định'),
            ('Củi cao su', 'Rubberwood firewood', 'Hevea brasiliensis', 'firewood', 'CUI_CS', 0, 0, 0.0, 850000, 'Mặc định'),
        ]
        
        for name, name_en, name_sci, wood_type, code, d_min, d_max, height, price, note in data:
            # 1. Tìm hoặc tạo/cập nhật Loài gỗ
            species = species_obj.search([('name', '=', name), ('company_id', '=', self.env.company.id)], limit=1)
            vals = {
                'name': name,
                'name_en': name_en,
                'name_sci': name_sci,
                'wood_type': wood_type,
                'code': code,
                'company_id': self.env.company.id
            }
            if species:
                species.write(vals)
            else:
                species = species_obj.create(vals)
                
            # 2. Tìm hoặc tạo/cập nhật Phân loại chất lượng loài gỗ
            grade = grade_obj.search([('species_id', '=', species.id), ('name', '=', note)], limit=1)
            grade_vals = {
                'species_id': species.id,
                'name': note,
                'diameter_min': d_min,
                'diameter_max': d_max,
                'height': height,
                'default_price': price,
                'note': note
            }
            if grade:
                grade.write(grade_vals)
            else:
                grade_obj.create(grade_vals)
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành công'),
                'message': _('Đã khởi tạo/cập nhật danh mục loài gỗ và phân loại thành công.'),
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
