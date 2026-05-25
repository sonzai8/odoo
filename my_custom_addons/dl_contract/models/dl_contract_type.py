# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DlContractType(models.Model):
    _name = 'dl.contract.type'
    _description = 'Loại hợp đồng lao động'
    _order = 'sequence, id'

    name = fields.Char(string='Tên loại hợp đồng', required=True, translate=True)
    code = fields.Char(string='Mã loại', required=True, copy=False)
    duration_type = fields.Selection([
        ('fixed', 'Có thời hạn'),
        ('indefinite', 'Vô thời hạn')
    ], string='Thời hạn', default='fixed', required=True)
    default_duration_months = fields.Integer(string='Thời hạn mặc định (tháng)', default=12)
    description = fields.Text(string='Mô tả chi tiết')
    template_id = fields.Many2one('dl.contract.template', string='Template mặc định', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    active = fields.Boolean(default=True, string='Đang sử dụng')
    sequence = fields.Integer(default=10, string='Thứ tự')
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company, index=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    default_wage = fields.Monetary(string='Lương cơ bản mặc định', currency_field='currency_id')

    _code_company_uniq = models.Constraint(
        'UNIQUE (code, company_id)', 
        'Mã loại hợp đồng phải là duy nhất trong cùng một công ty!'
    )
