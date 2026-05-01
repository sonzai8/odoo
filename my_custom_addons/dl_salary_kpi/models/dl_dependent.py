# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DLDependent(models.Model):
    _name = 'dl.dependent'
    _description = 'Người phụ thuộc'
    _order = 'employee_id, name'

    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True, ondelete='cascade')
    employee_tax_id = fields.Char(related='employee_id.dl_tax_id', string='MST Nhân viên', store=True)
    employee_tax_department_id = fields.Many2one('dl.tax.department', related='employee_id.dl_tax_department_id', string='Phòng ban thuế', store=True)
    employee_tax_position = fields.Char(related='employee_id.dl_tax_position', string='Chức vụ thuế', store=True)
    name = fields.Char(string='Họ và tên', required=True)
    birthday = fields.Date(string='Ngày sinh')
    relationship = fields.Selection([
        ('child', 'Con'),
        ('spouse', 'Vợ/Chồng'),
        ('parent', 'Bố/Mẹ'),
        ('sibling', 'Anh/Chị/Em'),
        ('other', 'Khác')
    ], string='Quan hệ', default='child', required=True)
    dependent_number = fields.Char(string='Mã số thuế NPT')
    dependent_id_card = fields.Char(string='CCCD NPT')
    date_from = fields.Date(string='Từ tháng', help='Tháng bắt đầu giảm trừ')
    date_to = fields.Date(string='Đến tháng', help='Tháng kết thúc giảm trừ')
    note = fields.Text(string='Ghi chú')
    active = fields.Boolean(string='Còn hiệu lực', default=True)

    def action_export_excel(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/dl_salary_kpi/export_dependents',
            'target': 'new',
        }
