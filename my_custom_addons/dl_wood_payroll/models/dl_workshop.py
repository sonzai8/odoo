# -*- coding: utf-8 -*-
from odoo import models, fields

class DlWorkshop(models.Model):
    _name = 'dl.workshop'
    _description = 'Xưởng sản xuất'
    _order = 'name'

    name = fields.Char(string='Tên xưởng', required=True)
    code = fields.Char(string='Mã xưởng')
    manager_id = fields.Many2one('hr.employee', string='Quản đốc')
    active = fields.Boolean(default=True)
    
    x_department_ids = fields.One2many(
        'hr.department', 
        'x_workshop_id', 
        string='Các bộ phận/Công đoạn'
    )
    
    description = fields.Text(string='Ghi chú')
