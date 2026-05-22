# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    x_wood_prefix = fields.Char(
        related='company_id.x_wood_prefix',
        string='Mã công ty',
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
    x_inventory_inspector = fields.Char(
        related='company_id.x_inventory_inspector',
        string='Người kiểm kê',
        readonly=False
    )
    x_inventory_inspector_position = fields.Char(
        related='company_id.x_inventory_inspector_position',
        string='Chức danh người kiểm kê',
        readonly=False
    )
