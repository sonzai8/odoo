# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class DlSalaryKpiLockWizard(models.TransientModel):
    _name = 'dl.salary.kpi.lock.wizard'
    _description = 'Cửa sổ chốt điểm KPI theo Tổ/Phòng ban'

    month_id = fields.Many2one('dl.salary.kpi.month', string='Bảng lương', required=True)
    department_id = fields.Many2one('dl.tax.department', string='Tổ / Phòng ban', required=True)
    action_type = fields.Selection([
        ('lock', 'Chốt điểm KPI'),
        ('unlock', 'Mở chốt điểm KPI')
    ], string='Hành động', default='lock', required=True)

    def action_confirm(self):
        self.ensure_one()
        domain = [
            ('month_id', '=', self.month_id.id),
            ('dl_tax_department_id', '=', self.department_id.id)
        ]
        lines = self.env['dl.salary.kpi.line'].search(domain)
        
        if not lines:
            raise UserError(_("Không tìm thấy nhân viên nào thuộc tổ này trong bảng lương hiện tại."))
            
        if self.action_type == 'lock':
            lines.action_lock_kpi_lines()
        else:
            lines.action_unlock_kpi_lines()
            
        return {'type': 'ir.actions.act_window_close'}
