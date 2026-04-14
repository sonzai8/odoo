# -*- coding: utf-8 -*-
from odoo import models, fields

class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    x_is_nhat_van = fields.Boolean(
        string='Là bộ phận Nhặt ván (Depr)', 
        default=False,
        help='DEPRECATED: Dùng thuộc tính trên Department thay thế'
    )
