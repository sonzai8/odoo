# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DailyPoolingResult(models.Model):
    _name = 'dl.daily.pooling.result'
    _description = 'Kết quả cào bằng lương tổ hàng ngày'
    _order = 'date desc, source_group_id, employee_id'

    date = fields.Date(string='Ngày', required=True, index=True)
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True)
    source_group_id = fields.Many2one('dl.production.group', string='Tổ gốc', required=True)
    workshop_id = fields.Many2one(
        related='source_group_id.x_workshop_id',
        string='Xưởng',
        store=True,
        index=True
    )
    
    actual_work_days = fields.Float(string='Số công thực tế')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)
    contribution_amount = fields.Monetary(string='Tổng tiền làm ra (Yield)', currency_field='currency_id')
    
    native_contribution = fields.Monetary(string='Tiền tại tổ', currency_field='currency_id')
    borrowed_contribution = fields.Monetary(string='Tiền mang về', currency_field='currency_id')
    is_loaned_worker = fields.Boolean(string='Đi làm thuê', index=True)
    
    # Pooling info
    pool_unit_price = fields.Monetary(string='Đơn giá 1 công (Tổ)', currency_field='currency_id')
    final_salary = fields.Monetary(string='Lương thực nhận', currency_field='currency_id')

    _sql_constraints = [
        ('date_employee_unique', 'unique(date, employee_id)', 'Kết quả của nhân viên này trong ngày này đã tồn tại!')
    ]
