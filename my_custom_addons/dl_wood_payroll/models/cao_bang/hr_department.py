# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HrDepartment(models.Model):
    _inherit = 'hr.department'
    _description = 'Department Extension for Wood Production'

    x_workshop_id = fields.Many2one(
        'dl.workshop', 
        string='Xưởng sản xuất', 
        help='Xưởng quản lý công đoạn này'
    )
    
    x_production_group_ids = fields.One2many(
        'dl.production.group', 
        'department_id', 
        string='Các tổ sản xuất'
    )
    
    x_is_production_stage = fields.Boolean(
        string='Là công đoạn sản xuất', 
        default=True,
        index=True
    )

    x_is_nhat_van = fields.Boolean(
        string='Là bộ phận Nhặt ván', 
        default=False,
        help='Nếu True, áp dụng logic tính đơn giá lũy tiến cho sản lượng > 280'
    )
