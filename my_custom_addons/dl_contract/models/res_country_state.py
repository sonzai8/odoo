# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResCountryState(models.Model):
    _inherit = 'res.country.state'
    
    x_sequence = fields.Integer(string='Thứ tự hiển thị', default=1000)
    x_gso_code = fields.Char(string='Mã GSO')
    x_gso_name = fields.Char(string='Mã - Tên Tỉnh', compute='_compute_x_gso_name', store=True)
    x_ward_ids = fields.One2many('res.country.ward', 'state_id', string='Xã/Phường')
    x_ward_count = fields.Integer(string='Số lượng xã', compute='_compute_x_ward_count', store=True)

    _order = 'x_sequence ASC, code ASC, name ASC'

    @api.depends('x_gso_code', 'name')
    def _compute_x_gso_name(self):
        for rec in self:
            if rec.x_gso_code:
                rec.x_gso_name = f"{rec.x_gso_code} - {rec.name}"
            else:
                rec.x_gso_name = rec.name

    @api.depends('x_ward_ids')
    def _compute_x_ward_count(self):
        for rec in self:
            rec.x_ward_count = len(rec.x_ward_ids)
