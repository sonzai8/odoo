# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

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
            species = species_obj.search([('name', '=', name)], limit=1)
            vals = {
                'name': name,
                'name_en': name_en,
                'name_sci': name_sci,
                'wood_type': wood_type,
                'code': code,
            }
            if species:
                species.write(vals)
            else:
                vals['company_id'] = self.env.company.id
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

    def action_init_peeling_types(self):
        """Khởi tạo danh sách danh mục ván bóc từ loài gỗ"""
        species = self.env['dl.wood.species'].search([])
        if species:
            return species.action_init_peeling_types()
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Chưa có loài gỗ'),
                'message': _('Vui lòng khởi tạo Danh mục Gỗ trước.'),
                'sticky': False,
                'type': 'warning',
            }
        }

    def action_init_report_templates(self):
        """Khởi tạo cấu hình phiên bản biểu mẫu v2026 cho công ty hiện tại"""
        version_obj = self.env['dl.wood.report.version']
        template_obj = self.env['dl.wood.report.template.config']
        
        # 1. Tìm hoặc tạo phiên bản biểu mẫu v2026 cho công ty hiện tại
        version = version_obj.search([
            ('code', '=', 'v2026'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        
        if not version:
            version = version_obj.create({
                'name': 'v2026',
                'code': 'v2026',
                'company_id': self.env.company.id,
                'active': True
            })
        else:
            version.write({'name': 'v2026'})
        
        # 2. Khởi tạo danh sách mẫu tài liệu mặc định
        templates_data = [
            ('ptkt', 10, 'Phiếu thông tin khai thác', 'exploitation', True),
            ('hdsg', 20, 'DL Hợp đồng HSG', 'exploitation', True),
            ('bkls', 30, 'Bảng kê lâm sản TT26', 'exploitation', True),
            ('ddnx', 40, 'Đơn đề nghị xác nhận bảng kê lâm sản', 'exploitation', True),
            ('bbxm', 50, 'Biên bản xác minh nguồn gốc lâm sản', 'exploitation', True),
            ('chia_nho_bkls', 60, 'Chia nhỏ bảng kê', 'exploitation', True),
            ('pnk', 70, 'Phiếu nhập kho', 'logistics', True),
            ('bbbg', 80, 'Biên bản bàn giao', 'logistics', True),
            ('gbn', 90, 'Giấy biên nhận', 'logistics', False),
        ]
        
        for key, seq, name, category, is_enabled in templates_data:
            existing = template_obj.search([
                ('version_id', '=', version.id),
                ('template_key', '=', key)
            ], limit=1)
            vals = {
                'version_id': version.id,
                'sequence': seq,
                'name': name,
                'template_key': key,
                'category': category,
                'is_enabled': is_enabled
            }
            if existing:
                existing.write(vals)
            else:
                template_obj.create(vals)
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành công'),
                'message': _('Đã khởi tạo/cập nhật phiên bản biểu mẫu v2026 thành công.'),
                'sticky': False,
                'type': 'success',
            }
        }

    def action_init_vehicles(self):
        """Khởi tạo danh sách xe vận chuyển cơ bản"""
        vehicle_obj = self.env['dl.wood.vehicle']
        
        data = [
            ('Xe 10 khối', 10.0, 98.0, 99.0, True),
            ('Xe 20 khối', 20.0, 98.0, 99.0, True),
            ('Xe 30 khối', 30.0, 98.0, 99.0, True),
        ]
        
        for name, capacity, fill_min, fill_max, active in data:
            existing = vehicle_obj.search([('name', '=', name), ('company_id', '=', self.env.company.id)], limit=1)
            vals = {
                'name': name,
                'capacity': capacity,
                'fill_rate_min': fill_min,
                'fill_rate_max': fill_max,
                'active': active,
                'company_id': self.env.company.id
            }
            if existing:
                existing.write(vals)
            else:
                vehicle_obj.create(vals)
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành công'),
                'message': _('Đã khởi tạo danh sách xe vận chuyển thành công.'),
                'sticky': False,
                'type': 'success',
            }
        }

    def action_init_state_sequence(self):
        """Khởi tạo thứ tự ưu tiên hiển thị cho các tỉnh thành Việt Nam"""
        priority_states = [
            'Bắc Ninh',
            'Lạng Sơn',
            'Quảng Ninh',
            'Thái Nguyên',
            'Nghệ An',
            'Tuyên Quang',
            'Hà Tĩnh',
            'Bắc Giang'
        ]
        state_obj = self.env['res.country.state']
        
        # Reset all VN states to 1000 first
        vn_states = state_obj.search([('country_id.code', '=', 'VN')])
        vn_states.write({'x_sequence': 1000})
        
        seq = 10
        for state_name in priority_states:
            # Search to match "Tỉnh Bắc Ninh" or just "Bắc Ninh"
            states = state_obj.search([
                ('country_id.code', '=', 'VN'), 
                '|', ('name', '=ilike', state_name), ('name', 'ilike', '%' + state_name)
            ])
            if states:
                states.write({'x_sequence': seq})
            seq += 10
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành công'),
                'message': _('Đã sắp xếp lại thứ tự ưu tiên Tỉnh/Thành phố thành công.'),
                'sticky': False,
                'type': 'success',
            }
        }

    def action_init_vietnam_wards(self):
        try:
            from vietnamadminunits.database.main import get_data
            ward_data = get_data(fields=['province', 'provinceCode', 'ward', 'wardCode'], table='admin_units')
        except Exception as e:
            raise UserError(_('Không thể đọc dữ liệu từ vietnamadminunits: %s') % str(e))
        
        state_obj = self.env['res.country.state']
        ward_obj = self.env['res.country.ward']
        partner_obj = self.env['res.partner']
        location_obj = self.env['dl.wood.exploitation.location']
        
        # Trước tiên, chuẩn hóa "Thừa Thiên - Huế" thành "Thành phố Huế"
        hue_state = state_obj.search([
            ('country_id.code', '=', 'VN'),
            ('name', 'in', ['Thừa Thiên - Huế', 'Thừa Thiên-Huế', 'Thừa Thiên Huế'])
        ], limit=1)
        if hue_state:
            hue_state.write({
                'name': 'Thành phố Huế',
                'x_gso_code': '46'
            })

        # 1. Cập nhật mã tỉnh và tên tỉnh đầy đủ cho các Tỉnh/Thành phố
        vn_states = state_obj.search([('country_id.code', '=', 'VN')])
        province_info_map = {}
        for item in ward_data:
            prov_name = item.get('province')
            prov_code = item.get('provinceCode')
            if prov_name and prov_code:
                province_info_map[prov_name.lower()] = (prov_code, prov_name)
                short_prov = prov_name.lower().replace('tỉnh ', '').replace('thành phố ', '').replace('tp ', '').strip()
                province_info_map[short_prov] = (prov_code, prov_name)

        for state in vn_states:
            state_name_lower = state.name.lower()
            info = province_info_map.get(state_name_lower)
            if not info:
                short_name = state_name_lower.replace('tỉnh ', '').replace('thành phố ', '').replace('tp ', '').strip()
                info = province_info_map.get(short_name)
            if info:
                gso_code, gso_full_name = info
                state.write({
                    'name': gso_full_name,
                    'x_gso_code': gso_code
                })

        # 2. Tạo mapping để tìm State ID từ tên
        state_map = {}
        for state in vn_states:
            state_map[state.name.lower()] = state.id
            name_lower = state.name.lower().replace('tỉnh ', '').replace('thành phố ', '').replace('tp ', '').strip()
            state_map[name_lower] = state.id
            
        created_count = 0
        updated_count = 0
        mapped_partners = 0
        mapped_locations = 0
        
        for item in ward_data:
            province_name = item.get('province', '').lower()
            ward_name = item.get('ward')
            ward_code = item.get('wardCode')
            
            if not ward_name:
                continue
                
            short_province = province_name.replace('tỉnh ', '').replace('thành phố ', '').replace('tp ', '').strip()
            state_id = state_map.get(short_province) or state_map.get(province_name)
            if not state_id:
                for key, val in state_map.items():
                    if key in short_province or short_province in key:
                        state_id = val
                        break
                        
            if state_id:
                # Kiểm tra tồn tại
                existing = ward_obj.search([('name', '=', ward_name), ('state_id', '=', state_id)], limit=1)
                if not existing:
                    existing = ward_obj.create({
                        'name': ward_name,
                        'state_id': state_id,
                        'x_gso_code': ward_code
                    })
                    created_count += 1
                else:
                    if existing.x_gso_code != ward_code:
                        existing.write({'x_gso_code': ward_code})
                        updated_count += 1
                
                # Mapping đối tác cũ (chỉ cần tìm chính xác chuỗi chứa ward_name)
                partners = partner_obj.search([
                    ('state_id', '=', state_id),
                    ('ward_id', '=', False),
                    ('city', 'ilike', ward_name)
                ])
                if partners:
                    partners.write({'ward_id': existing.id})
                    mapped_partners += len(partners)
                    
                locations = location_obj.search([
                    ('state_id', '=', state_id),
                    ('ward_id', '=', False),
                    ('city', 'ilike', ward_name)
                ])
                if locations:
                    locations.write({'ward_id': existing.id})
                    mapped_locations += len(locations)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Hoàn tất!'),
                'message': _('Đã tạo %s Xã mới, cập nhật mã cho %s Xã. Map tự động cho %s Đối tác và %s Địa điểm.') % (created_count, updated_count, mapped_partners, mapped_locations),
                'sticky': True,
                'type': 'success',
            }
        }

    def action_init_peeling_suppliers(self):
        """Khởi tạo danh sách Nhà Cung Cấp Ván Bóc mặc định.
        Kiểm tra trùng theo mã số thuế (vat). Nếu chưa có thì tạo mới, nếu có rồi thì bỏ qua.
        """
        import json
        import os
        from odoo.modules import get_module_path

        Partner = self.env['res.partner']
        country_vn = self.env['res.country'].search([('code', '=', 'VN')], limit=1)

        module_path = get_module_path('dl_wood_traceability')
        if not module_path:
            raise UserError(_('Không tìm thấy module dl_wood_traceability!'))
            
        file_path = os.path.join(module_path, 'data', 'peeling_suppliers.json')
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            raise UserError(_('Không thể đọc file dữ liệu peeling_suppliers.json: %s') % str(e))

        State = self.env['res.country.state']
        Ward = self.env['res.country.ward']
        created_count = 0
        skipped_count = 0

        for item in data:
            vat = item.get('ma_so_thue')
            if not vat:
                skipped_count += 1
                continue

            # Kiểm tra theo MST và công ty hiện tại
            existing = Partner.search([
                ('vat', '=', vat),
                '|', ('company_id', '=', False), ('company_id', '=', self.env.company.id)
            ], limit=1)
            if existing:
                skipped_count += 1
                continue

            is_company = item.get('type') == 'company'
            linh_vuc = (item.get('linh_vuc_hoat_dong') or '').strip()
            ten_rieng = (item.get('ten_rieng') or '').strip()
            
            if is_company and linh_vuc:
                name = f"{linh_vuc} {ten_rieng}".strip()
            else:
                name = ten_rieng

            dia_chi = item.get('dia_chi', {})
            thon_xom = dia_chi.get('thon_xom')
            xa_phuong = dia_chi.get('xa_phuong')
            tinh_thanh = dia_chi.get('tinh_thanh')

            state_id = False
            if tinh_thanh and country_vn:
                # Bỏ qua các từ khóa như 'Tỉnh', 'Thành phố' để search chính xác hơn nếu cần, nhưng ilike thường đủ
                state_record = State.search([('name', 'ilike', tinh_thanh.replace('Tỉnh', '').replace('Thành phố', '').strip()), ('country_id', '=', country_vn.id)], limit=1)
                if state_record:
                    state_id = state_record.id

            ward_id = False
            if xa_phuong and state_id:
                ward_record = Ward.search([('name', 'ilike', xa_phuong.replace('Xã', '').replace('Phường', '').replace('Thị trấn', '').strip()), ('state_id', '=', state_id)], limit=1)
                if ward_record:
                    ward_id = ward_record.id

            # Tạo mới
            Partner.create({
                'name': name,
                'vat': vat,
                'is_company': is_company,
                'x_is_peeling_supplier': True,
                'street': thon_xom,
                'ward_id': ward_id,
                'state_id': state_id,
                'country_id': country_vn.id if country_vn else False,
                'x_company_type_label': linh_vuc if is_company else False,
                'x_private_name': ten_rieng if is_company else False,
                'company_id': self.env.company.id,
            })
            created_count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Hoàn tất!'),
                'message': _('Đã tạo mới %s NCC Ván Bóc. Bỏ qua %s bản ghi đã tồn tại hoặc không có MST.') % (created_count, skipped_count),
                'sticky': False,
                'type': 'success',
            }
        }


