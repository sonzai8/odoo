# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SalaryKpiEmployee(models.Model):
    _name = 'dl.salary.kpi.employee'
    _description = 'Nhân viên KPI'
    _order = 'name'

    name = fields.Char(string='Họ và tên', required=True)
    employee_id = fields.Many2one('hr.employee', string='Nhân viên hệ thống')
    identification_id = fields.Char(string='Số CCCD', related='employee_id.identification_id', readonly=False, store=True)
    department_id = fields.Many2one('hr.department', string='Xưởng/Phòng ban', related='employee_id.department_id', readonly=False, store=True)
    work_group_id = fields.Many2one('dl.production.group', string='Tổ biên chế', related='employee_id.x_source_group_id', readonly=False, store=True)
    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác')
    ], string='Giới tính', default='male')
    default_att_type_id = fields.Many2one('dl.salary.kpi.attendance.type', string='Công mặc định')
    active = fields.Boolean(default=True)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.name = self.employee_id.name
            self.identification_id = self.employee_id.identification_id
            self.department_id = self.employee_id.department_id
            self.work_group_id = self.employee_id.x_source_group_id
            self.gender = self.employee_id.gender

    def action_sync_from_hr(self):
        hr_employees = self.env['hr.employee'].search([('active', '=', True)])
        kpi_employees = self.search([])
        kpi_map = {e.employee_id.id: e for e in kpi_employees if e.employee_id}
        
        new_count = 0
        updated_count = 0
        female_count = 0
        
        for emp in hr_employees:
            # Explicitly fetch gender from HR Selection (Odoo 19 uses 'sex' string='Gender')
            hr_gender = getattr(emp, 'sex', getattr(emp, 'gender', 'male')) or 'male'
            existing_kpi = kpi_map.get(emp.id)
            
            if existing_kpi:
                # Force update gender from HR
                if existing_kpi.gender != hr_gender:
                    existing_kpi.write({'gender': hr_gender})
                    updated_count += 1
            else:
                self.create({
                    'name': emp.name,
                    'employee_id': emp.id,
                    'gender': hr_gender,
                })
                new_count += 1
            
            if hr_gender == 'female':
                female_count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành công'),
                'message': _('Đã đồng bộ %s NV mới, cập nhật %s NV. (Tổng %s Nữ)') % (new_count, updated_count, female_count),
                'type': 'success',
            }
        }
