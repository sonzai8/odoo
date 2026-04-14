# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    x_source_group_id = fields.Many2one(
        'dl.production.group', 
        string='Tổ gốc', 
        tracking=True,
        help='Xác định tổ gốc biên chế của nhân viên'
    )
    x_is_daily_worker = fields.Boolean(
        string='Lao động thời vụ', 
        tracking=True,
        default=False
    )

    @api.onchange('x_source_group_id')
    def _onchange_x_source_group_id(self):
        if self.x_source_group_id and self.x_source_group_id.department_id:
            self.department_id = self.x_source_group_id.department_id
