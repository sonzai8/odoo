# -*- coding: utf-8 -*-
from odoo import models, fields, _

class DlContractInitWizard(models.TransientModel):
    _name = 'dl.contract.init.wizard'
    _description = 'Khởi tạo dữ liệu cơ bản cho Module Hợp đồng'

    def action_init_data(self):
        contract_type_obj = self.env['dl.contract.type']
        company = self.env.company

        # 1. Hợp đồng có thời hạn
        fixed_code = 'co_thoi_han'
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
        indefinite_code = 'vo_thoi_han'
        if not contract_type_obj.search_count([('code', '=', indefinite_code), ('company_id', '=', company.id)]):
            contract_type_obj.create({
                'name': 'Hợp đồng vô thời hạn',
                'code': indefinite_code,
                'duration_type': 'indefinite',
                'sequence': 20,
                'company_id': company.id,
            })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Thành công"),
                'message': _("Đã khởi tạo xong các Loại hợp đồng cơ bản cho công ty %s.") % company.name,
                'type': 'success',
                'sticky': False,
            }
        }
