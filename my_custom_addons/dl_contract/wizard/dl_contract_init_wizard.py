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
