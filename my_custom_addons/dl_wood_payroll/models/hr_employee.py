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

    @api.onchange('x_source_group_id')
    def _onchange_x_source_group_id(self):
        if self.x_source_group_id and self.x_source_group_id.department_id:
            self.department_id = self.x_source_group_id.department_id

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
