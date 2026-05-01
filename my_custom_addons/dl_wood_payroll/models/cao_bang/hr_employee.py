# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

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
    x_has_insurance = fields.Boolean(
        string='Đóng BH (BHYT/BHXH)',
        tracking=True,
        default=True,
        help='Đánh dấu nhân viên có tham gia đóng bảo hiểm. Nhân viên đóng BH và đi đủ công mới được hưởng đơn giá cao.'
    )

    @api.onchange('x_source_group_id')
    def _onchange_x_source_group_id(self):
        if self.x_source_group_id and self.x_source_group_id.department_id:
            self.department_id = self.x_source_group_id.department_id

    @api.depends('name', 'x_source_group_id.name')
    def _compute_display_name(self):
        for employee in self:
            if employee.x_source_group_id:
                employee.display_name = f"{employee.name} ({employee.x_source_group_id.name})"
            else:
                employee.display_name = employee.name

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=100, order=None):
        if name:
            domain = ['|', ('name', operator, name), ('x_source_group_id.name', operator, name)] + (domain or [])
        return super()._name_search(name, domain, operator, limit, order)

    def action_view_missing_attendance(self):
        """Trả về danh sách nhân viên chưa có chấm công trong ngày hiện tại"""
        today = fields.Date.today()
        # Lấy ID của tất cả nhân viên đã có chấm công hôm nay
        attended_emp_ids = self.env['dl.daily.attendance.line'].search([
            ('date', '=', today)
        ]).mapped('employee_id.id')
        
        return {
            'name': _('Nhân viên thiếu công hôm nay'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee',
            'view_mode': 'list,form',
            'domain': [('id', 'not in', attended_emp_ids)],
            'context': {'search_default_group_by_source_group': 1},
        }
