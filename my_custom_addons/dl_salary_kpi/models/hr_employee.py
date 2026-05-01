# -*- coding: utf-8 -*-
from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Override name
    
    dl_first_name = fields.Char(string="Tên riêng", help="Nhập tên riêng của nhân viên")
    dl_tax_id = fields.Char(string='Mã số thuế')
    dl_tax_department_id = fields.Many2one('dl.tax.department', string='Phòng ban thuế')
    dl_tax_position = fields.Char(string='Chức vụ thuế')
    dl_tax_base_salary = fields.Float(string='Lương cơ bản thuế')
    dl_departure_date = fields.Date(string='Ngày nghỉ việc')
    dependent_ids = fields.One2many('dl.dependent', 'employee_id', string='Người phụ thuộc')
