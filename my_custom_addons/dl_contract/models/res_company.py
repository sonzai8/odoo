# -*- coding: utf-8 -*-
from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    x_kcb_state_id = fields.Many2one('res.country.state', string='Tỉnh đăng ký KCB mặc định', domain="[('country_id.code', '=', 'VN')]")
    x_kcb_hospital = fields.Char(string='Bệnh viện đăng ký KCB mặc định')
