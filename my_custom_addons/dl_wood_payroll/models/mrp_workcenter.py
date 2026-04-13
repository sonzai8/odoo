# -*- coding: utf-8 -*-
from odoo import models, fields

class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    x_is_nhat_van = fields.Boolean(
        string='Là bộ phận Nhặt ván', 
        default=False,
        help='Nếu True, áp dụng logic tính đơn giá lũy tiến cho sản lượng > 280'
    )
    x_workshop_id = fields.Many2one('dl.workshop', string='Xưởng')
    x_production_group_ids = fields.One2many(
        'dl.production.group', 
        'work_center_id', 
        string='Danh sách Tổ'
    )
