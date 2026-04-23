# -*- coding: utf-8 -*-
from odoo import models, fields

class DlTaxDepartment(models.Model):
    _name = 'dl.tax.department'
    _description = 'Phòng ban thuế'
    _order = 'sequence, name'

    name = fields.Char(string='Tên phòng ban', required=True)
    code = fields.Char(string='Mã phòng ban')
    sequence = fields.Integer(string='Thứ tự', default=10)
    active = fields.Boolean(string='Đang hoạt động', default=True)

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Tên phòng ban đã tồn tại!')
    ]
