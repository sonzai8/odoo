# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SalaryKpiAttendanceType(models.Model):
    _name = 'dl.salary.kpi.attendance.type'
    _description = 'Loại công KPI'
    _rec_name = 'code'
    _order = 'sequence'

    code = fields.Char(string='Mã', required=True)
    name = fields.Char(string='Tên đầy đủ', required=True)
    sequence = fields.Integer(default=10)
    
    num_work = fields.Float(string='Số công', default=0.0, help="Số công tính được khi chấm loại công này (VD: 1.0, 0.5)")
    day_hour = fields.Float(string='Giờ ngày', default=0.0)
    night_hour = fields.Float(string='Giờ đêm', default=0.0)
    default_overtime = fields.Float(string='OT mặc định', default=0.0, help="Giờ tăng ca mặc định của công này")

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Mã loại công đã tồn tại!')
    ]
