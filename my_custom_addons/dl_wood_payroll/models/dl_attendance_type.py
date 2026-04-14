# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AttendanceType(models.Model):
    _name = 'dl.attendance.type'
    _description = 'Loại hình chấm công'
    _order = 'sequence, id'

    name = fields.Char(string='Tên loại công', required=True)
    code = fields.Char(string='Ký hiệu', required=True, help="Ví dụ: N, D, P, K")
    work_value = fields.Float(string='Giá trị quy đổi công', default=1.0, 
                             help="Dùng để tính tổng công thực tế. Ví dụ: 1.0, 0.5, 0.0")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Ký hiệu chấm công đã tồn tại!')
    ]
