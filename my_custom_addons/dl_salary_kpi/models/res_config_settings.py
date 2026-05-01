# -*- coding: utf-8 -*-
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    dl_pit_personal_deduction = fields.Monetary(
        related='company_id.dl_pit_personal_deduction',
        string='Giảm trừ bản thân',
        readonly=False
    )
    dl_pit_dependent_deduction = fields.Monetary(
        related='company_id.dl_pit_dependent_deduction',
        string='Giảm trừ người phụ thuộc',
        readonly=False
    )
