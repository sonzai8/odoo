# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProductionGroup(models.Model):
    _name = 'dl.production.group'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Tổ sản xuất'
    _order = 'work_center_id, name'

    name = fields.Char(string='Tên tổ', required=True, tracking=True)
    work_center_id = fields.Many2one(
        'mrp.workcenter', 
        string='Công đoạn', 
        required=True, 
        tracking=True
    )
    x_workshop_id = fields.Many2one(
        related='work_center_id.x_workshop_id',
        string='Xưởng',
        store=True,
        readonly=True
    )
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
    
    # Virtual field for selection UI
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
            # Employees being added to this group
            added = group.x_employee_ids - group.member_ids
            if added:
                added.write({'x_source_group_id': group.id})
            
            # Employees being removed from this group
            removed = group.member_ids - group.x_employee_ids
            if removed:
                removed.write({'x_source_group_id': False})

    @api.depends('member_ids')
    def _compute_member_count(self):
        for group in self:
            group.member_count = len(group.member_ids)
