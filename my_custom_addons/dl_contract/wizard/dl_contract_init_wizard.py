# -*- coding: utf-8 -*-
from odoo import models, fields, _

class DlContractInitWizard(models.TransientModel):
    _name = 'dl.contract.init.wizard'
    _description = 'Khởi tạo dữ liệu cơ bản cho Module Hợp đồng'

    def action_init_data(self):
        contract_type_obj = self.env['dl.contract.type']
        company = self.env.company

        # 1. Hợp đồng có thời hạn
        fixed_code = 'CTH'
        if not contract_type_obj.search_count([('code', '=', fixed_code), ('company_id', '=', company.id)]):
            contract_type_obj.create({
                'name': 'Hợp đồng có thời hạn',
                'code': fixed_code,
                'duration_type': 'fixed',
                'default_duration_months': 12,
                'sequence': 10,
                'company_id': company.id,
                'default_wage': 6100000,
            })

        # 2. Hợp đồng vô thời hạn
        indefinite_code = 'KTH'
        if not contract_type_obj.search_count([('code', '=', indefinite_code), ('company_id', '=', company.id)]):
            contract_type_obj.create({
                'name': 'Hợp đồng vô thời hạn',
                'code': indefinite_code,
                'duration_type': 'indefinite',
                'sequence': 20,
                'company_id': company.id,
            })

        # 3. Khởi tạo Phòng ban
        dept_obj = self.env['hr.department']
        
        admin_dept = dept_obj.search([('name', '=', 'Bộ phận hành chính'), ('company_id', '=', company.id)], limit=1)
        if not admin_dept:
            admin_dept = dept_obj.create({
                'name': 'Bộ phận hành chính',
                'company_id': company.id,
            })
            
        prod_dept = dept_obj.search([('name', '=', 'Bộ phận sản xuất'), ('company_id', '=', company.id)], limit=1)
        if not prod_dept:
            prod_dept = dept_obj.create({
                'name': 'Bộ phận sản xuất',
                'company_id': company.id,
            })

        # 4. Khởi tạo Chức danh
        job_obj = self.env['dl.job.title']
        
        admin_jobs = [
            ('giam_doc', 'Giám đốc'),
            ('ke_toan', 'Nhân viên kế toán'),
            ('quan_ly', 'Nhân viên quản lý'),
            ('van_phong', 'Nhân viên văn phòng'),
            ('kinh_doanh', 'Nhân viên kinh doanh'),
            ('thu_kho', 'Thủ kho'),
        ]
        for code, name in admin_jobs:
            if not job_obj.search_count([('code', '=', code), ('company_id', '=', company.id)]):
                job_obj.create({
                    'name': name,
                    'code': code,
                    'department_id': admin_dept.id,
                    'company_id': company.id,
                })
                
        prod_jobs = [
            ('cong_nhan', 'Công nhân sản xuất'),
        ]
        for code, name in prod_jobs:
            if not job_obj.search_count([('code', '=', code), ('company_id', '=', company.id)]):
                job_obj.create({
                    'name': name,
                    'code': code,
                    'department_id': prod_dept.id,
                    'company_id': company.id,
                })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Thành công"),
                'message': _("Đã khởi tạo xong các phòng ban, chức danh và loại hợp đồng cơ bản cho công ty %s.") % company.name,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_init_vietnam_wards(self):
        from odoo.exceptions import UserError
        try:
            from vietnamadminunits.database.main import get_data
            ward_data = get_data(fields=['province', 'provinceCode', 'ward', 'wardCode'], table='admin_units')
        except Exception as e:
            raise UserError(_('Không thể đọc dữ liệu từ vietnamadminunits: %s') % str(e))
        
        state_obj = self.env['res.country.state']
        ward_obj = self.env['res.country.ward']
        
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

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Hoàn tất!'),
                'message': _('Đã tạo %s Xã mới, cập nhật mã cho %s Xã thành công.') % (created_count, updated_count),
                'sticky': True,
                'type': 'success',
            }
        }
