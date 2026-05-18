# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    x_wood_prefix = fields.Char(
        related='company_id.x_wood_prefix',
        string='Tiền tố mã Gỗ',
        readonly=False
    )
    x_representative = fields.Char(
        related='company_id.x_representative',
        string='Người đại diện công ty',
        readonly=False
    )
    x_representative_position = fields.Char(
        related='company_id.x_representative_position',
        string='Chức vụ đại diện',
        readonly=False
    )
