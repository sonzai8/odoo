# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class DlVietnamBank(models.Model):
    _name = 'dl.vietnam.bank'
    _description = 'Ngân hàng Việt Nam'
    _inherit = ['dl.wood.log.mixin']
    _order = 'sequence, name, id'
    _rec_names_search = ['name', 'short_name', 'code']

    name = fields.Char(string='Tên ngân hàng đầy đủ', required=True)
    short_name = fields.Char(string='Tên ngân hàng viết tắt', required=True, index=True)
    code = fields.Char(string='Mã ngân hàng (Swift/Citad)', index=True)
    sequence = fields.Integer(string='Độ phổ biến', default=10)
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company)
    active = fields.Boolean(string='Có hiệu lực', default=True)

    _sql_constraints = [
        ('uniq_short_name', 'unique(short_name, company_id)', 'Tên viết tắt ngân hàng đã tồn tại!')
    ]

    @api.depends('name', 'short_name')
    def _compute_display_name(self):
        for bank in self:
            if bank.short_name and bank.name:
                bank.display_name = f"{bank.short_name} - {bank.name}"
            else:
                bank.display_name = bank.short_name or bank.name or ""
