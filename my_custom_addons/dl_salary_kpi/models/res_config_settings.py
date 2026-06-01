# -*- coding: utf-8 -*-
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    dl_pit_personal_deduction = fields.Monetary(
        related='company_id.dl_pit_personal_deduction',
        string='Giảm trừ bản thân',
        readonly=False
    )
    dl_pit_dependent_deduction = fields.Monetary(
        related='company_id.dl_pit_dependent_deduction',
        string='Giảm trừ người phụ thuộc',
        readonly=False
    )
    def action_standardize_tax_departments(self):
        """Chuẩn hóa lại phòng ban thuế cho toàn bộ nhân viên của công ty hiện tại."""
        company = self.env.company
        employees = self.env['hr.employee'].sudo().search([
            ('company_id', '=', company.id),
            ('dl_tax_department_id', '!=', False)
        ])
        count = 0
        for emp in employees:
            current_dept = emp.dl_tax_department_id
            if current_dept.company_id != company:
                # Tìm phòng ban cùng tên ở đúng công ty hiện tại
                correct_dept = self.env['dl.tax.department'].sudo().search([
                    ('name', '=', current_dept.name),
                    ('company_id', '=', company.id)
                ], limit=1)
                
                if correct_dept:
                    emp.sudo().write({'dl_tax_department_id': correct_dept.id})
                    count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Hoàn tất chuẩn hóa',
                'message': f'Đã cập nhật đúng phòng ban cho {count} nhân viên.',
                'sticky': False,
                'type': 'success',
            }
        }


