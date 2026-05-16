# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    x_wood_prefix = fields.Char(
        related='company_id.x_wood_prefix',
        string='Tiền tố mã Gỗ',
        readonly=False
    )
