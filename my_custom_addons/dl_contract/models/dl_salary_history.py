# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DlSalaryHistory(models.Model):
    _name = 'dl.salary.history'
    _description = 'Lịch sử điều chỉnh lương'
    _order = 'effective_date desc, id desc'

    contract_id = fields.Many2one('dl.contract', string='Hợp đồng', required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', related='contract_id.employee_id', store=True)
    company_id = fields.Many2one('res.company', string='Công ty', related='contract_id.company_id', store=True)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', related='company_id.currency_id')
    
    old_wage = fields.Monetary(string='Lương cũ')
    new_wage = fields.Monetary(string='Lương mới', required=True)
    difference = fields.Monetary(string='Chênh lệch', compute='_compute_difference')
    
    effective_date = fields.Date(string='Ngày hiệu lực', required=True, default=fields.Date.context_today)
    reason = fields.Text(string='Lý do điều chỉnh')
    user_id = fields.Many2one('res.users', string='Người thực hiện', default=lambda self: self.env.user)
    note = fields.Char(string='Ghi chú thêm')

    @api.depends('old_wage', 'new_wage')
    def _compute_difference(self):
        for record in self:
            record.difference = record.new_wage - record.old_wage
