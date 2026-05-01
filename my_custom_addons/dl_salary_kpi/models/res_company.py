# -*- coding: utf-8 -*-
from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    dl_pit_personal_deduction = fields.Monetary(string='Giảm trừ bản thân', default=15500000, currency_field='currency_id')
    dl_pit_dependent_deduction = fields.Monetary(string='Giảm trừ người phụ thuộc', default=6200000, currency_field='currency_id')
