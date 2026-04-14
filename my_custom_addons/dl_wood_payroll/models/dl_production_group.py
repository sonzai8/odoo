# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProductionGroup(models.Model):
    _name = 'dl.production.group'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Tổ sản xuất'
    _order = 'department_id, name'

    name = fields.Char(string='Tên tổ', required=True, tracking=True)
    department_id = fields.Many2one(
        'hr.department', 
        string='Công đoạn sản xuất', 
        required=True, 
        tracking=True,
        domain=[('x_is_production_stage', '=', True)]
    )
    x_workshop_id = fields.Many2one(
        'dl.workshop',
        string='Xưởng',
        store=True,
        tracking=True
    )

    @api.onchange('department_id')
    def _onchange_department_id(self):
        if self.department_id and self.department_id.x_workshop_id:
            self.x_workshop_id = self.department_id.x_workshop_id

    @api.onchange('x_workshop_id')
    def _onchange_x_workshop_id(self):
        # Clear department if it doesn't match the new workshop
        if self.department_id and self.department_id.x_workshop_id != self.x_workshop_id:
            self.department_id = False
    leader_id = fields.Many2one(
        'hr.employee', 
        string='Tổ trưởng', 
        tracking=True
    )
    member_ids = fields.One2many(
        'hr.employee', 
        'x_source_group_id', 
        string='Danh sách nhân viên'
    )
    
    x_employee_ids = fields.Many2many(
        'hr.employee', 
        string='Thành viên', 
        compute='_compute_x_employee_ids', 
        inverse='_inverse_x_employee_ids',
        help='Chọn nhân viên để biên chế vào tổ này'
    )
    
    active = fields.Boolean(default=True)
    
    member_count = fields.Integer(
        string='Số lượng thành viên', 
        compute='_compute_member_count'
    )

    @api.depends('member_ids')
    def _compute_x_employee_ids(self):
        for group in self:
            group.x_employee_ids = group.member_ids

    def _inverse_x_employee_ids(self):
        for group in self:
            added = group.x_employee_ids - group.member_ids
            if added:
                added.write({
                    'x_source_group_id': group.id,
                    'department_id': group.department_id.id
                })
            
            removed = group.member_ids - group.x_employee_ids
            if removed:
                removed.write({'x_source_group_id': False})

    @api.depends('member_ids')
    def _compute_member_count(self):
        for group in self:
            group.member_count = len(group.member_ids)
