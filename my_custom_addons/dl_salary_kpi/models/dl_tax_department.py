# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.models import Constraint

class DlTaxDepartment(models.Model):
    _name = 'dl.tax.department'
    _description = 'Phòng ban thuế'
    _order = 'sequence, name'

    name = fields.Char(string='Tên phòng ban', required=True)
    code = fields.Char(string='Mã phòng ban')
    sequence = fields.Integer(string='Thứ tự', default=10)
    active = fields.Boolean(string='Đang hoạt động', default=True)
    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company)

    _name_unique = Constraint('unique(name)', 'Tên phòng ban đã tồn tại!')
