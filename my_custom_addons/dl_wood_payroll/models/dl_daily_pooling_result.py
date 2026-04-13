# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DailyPoolingResult(models.Model):
    _name = 'dl.daily.pooling.result'
    _description = 'Kết quả cào bằng lương tổ hàng ngày'
    _order = 'date desc, source_group_id, employee_id'

    date = fields.Date(string='Ngày', required=True, index=True)
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True)
    source_group_id = fields.Many2one('mrp.workcenter', string='Tổ gốc', required=True)
    
    actual_work_days = fields.Float(string='Số công thực tế')
    contribution_amount = fields.Float(string='Tiền làm ra (Yield)')
    
    # Pooling info
    pool_unit_price = fields.Float(string='Đơn giá 1 công (Tổ)')
    final_salary = fields.Float(string='Lương thực nhận')

    _month_year_unique = models.Constraint(
        "UNIQUE(date, employee_id)",
        "Kết quả cho nhân viên này trong ngày này đã tồn tại!"
    )
