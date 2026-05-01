# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class StevedoreTask(models.Model):
    _name = 'dl.stevedore.task'
    _description = 'Danh mục công việc bốc vác'
    _order = 'name'

    name = fields.Char(string='Tên công việc', required=True)
    uom_id = fields.Many2one('uom.uom', string='Đơn vị tính', required=True)
    unit_price = fields.Float(string='Đơn giá')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)
    note = fields.Text(string='Ghi chú')
    active = fields.Boolean(default=True)
