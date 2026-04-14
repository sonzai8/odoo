# -*- coding: utf-8 -*-
from odoo import models, fields, api

class FineReason(models.Model):
    _name = 'dl.fine.reason'
    _description = 'Lý do phạt'
    _order = 'sequence, id'

    name = fields.Char(string='Lý do', required=True)
    default_amount = fields.Float(string='Mức phạt mặc định', default=0.0)
    sequence = fields.Integer(default=10)

class EmployeeFine(models.Model):
    _name = 'dl.employee.fine'
    _description = 'Phiếu phạt nhân viên'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Mã phiếu', copy=False, readonly=True, default='NEW')
    date = fields.Date(string='Ngày vi phạm', default=fields.Date.today(), required=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Nhân viên bị phạt', required=True, tracking=True)
    reason_id = fields.Many2one('dl.fine.reason', string='Lý do phạt', tracking=True)
    description = fields.Text(string='Mô tả chi tiết', tracking=True)
    amount = fields.Float(string='Số tiền phạt', required=True, tracking=True)

    @api.onchange('reason_id')
    def _onchange_reason_id(self):
        if self.reason_id:
            self.amount = self.reason_id.default_amount

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'NEW') == 'NEW':
                vals['name'] = self.env['ir.sequence'].next_by_code('dl.employee.fine') or '/'
        return super().create(vals_list)
