# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResCountryWard(models.Model):
    _name = 'res.country.ward'
    _description = 'Xã / Phường'
    _order = 'state_id, name'

    name = fields.Char(string='Tên Xã/Phường', required=True)
    state_id = fields.Many2one('res.country.state', string='Tỉnh/Thành phố', required=True, ondelete='cascade')
    active = fields.Boolean(default=True)
    
    x_gso_code = fields.Char(string='Mã GSO')
    x_gso_name = fields.Char(string='Mã - Tên Xã', compute='_compute_x_gso_name', store=True)

    _sql_constraints = [
        ('name_state_uniq', 'unique(name, state_id)', 'Tên Xã/Phường đã tồn tại trong Tỉnh/Thành phố này!')
    ]

    @api.depends('x_gso_code', 'name')
    def _compute_x_gso_name(self):
        for rec in self:
            if rec.x_gso_code:
                rec.x_gso_name = f"{rec.x_gso_code} - {rec.name}"
            else:
                rec.x_gso_name = rec.name
