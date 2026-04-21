# -*- coding: utf-8 -*-
from odoo import models, fields

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    x_wood_pickup_id = fields.Many2one('dl.wood.pickup.production', string='Phiếu Nhặt ván', ondelete='set null')
