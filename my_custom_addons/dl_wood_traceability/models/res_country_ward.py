# -*- coding: utf-8 -*-
from odoo import models, fields

class ResCountryWard(models.Model):
    _name = 'res.country.ward'
    _description = 'Xã / Phường'
    _order = 'state_id, name'

    name = fields.Char(string='Tên Xã/Phường', required=True)
    state_id = fields.Many2one('res.country.state', string='Tỉnh/Thành phố', required=True, ondelete='cascade')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_state_uniq', 'unique(name, state_id)', 'Tên Xã/Phường đã tồn tại trong Tỉnh/Thành phố này!')
    ]
