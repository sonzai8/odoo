# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DlJobTitle(models.Model):
    _name = 'dl.job.title'
    _description = 'Chức danh công việc'
    _order = 'sequence, id'

    name = fields.Char(string='Tên chức danh', required=True)
    code = fields.Char(string='Mã chức danh', required=True)
    department_id = fields.Many2one('hr.department', string='Phòng ban', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    sequence = fields.Integer(string='Thứ tự', default=10)
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company, index=True)

    _code_company_uniq = models.Constraint(
        'UNIQUE (code, company_id)', 
        'Mã chức danh phải là duy nhất trong cùng một công ty!'
    )
