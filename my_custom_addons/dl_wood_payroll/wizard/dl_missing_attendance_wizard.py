# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class MissingAttendanceWizard(models.TransientModel):
    _name = 'dl.missing.attendance.wizard'
    _description = 'Wizard kiểm tra thiếu chấm công'

    date = fields.Date(string='Ngày kiểm tra', default=fields.Date.today(), required=True)
    department_id = fields.Many2one('hr.department', string='Bộ phận/Công đoạn')

    def action_view(self):
        self.ensure_one()
        # 1. Tìm tất cả nhân viên đã có chấm công vào ngày này
        attended_ids = self.env['dl.daily.attendance.line'].search([
            ('date', '=', self.date)
        ]).mapped('employee_id.id')

        # 2. Xây dựng domain
        domain = [('id', 'not in', attended_ids)]
        
        # 3. Lọc thêm theo phòng ban nếu có chọn
        if self.department_id:
            domain.append(('department_id', 'child_of', self.department_id.id))

        return {
            'name': _('Nhân viên thiếu công ngày %s') % self.date,
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {
                'search_default_group_by_source_group': 1,
                'create': False, # Không cho phép tạo mới từ màn hình này để tránh nhầm lẫn
            },
            'target': 'current',
        }
