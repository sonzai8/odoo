# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SalaryKpiLnbWizard(models.TransientModel):
    _name = 'dl.salary.kpi.lnb.wizard'
    _description = 'Wizard Sửa nhanh Lương Nội Bộ (LNB)'

    line_id = fields.Many2one('dl.salary.kpi.line', string='Dòng lương', required=True, ondelete='cascade')
    employee_name = fields.Char(related='line_id.employee_name', string='Nhân viên', readonly=True)
    identification_id = fields.Char(related='line_id.identification_id', string='Số CCCD', readonly=True)
    currency_id = fields.Many2one('res.currency', related='line_id.currency_id')

    current_lnb = fields.Monetary(related='line_id.payroll_internal_salary', string='LNB Hiện tại', readonly=True, currency_field='currency_id')
    new_lnb = fields.Monetary(string='LNB Mới', required=True, currency_field='currency_id')

    @api.model
    def default_get(self, fields_list):
        res = super(SalaryKpiLnbWizard, self).default_get(fields_list)
        if self._context.get('active_id'):
            line = self.env['dl.salary.kpi.line'].browse(self._context.get('active_id'))
            res.update({
                'line_id': line.id,
                'new_lnb': line.payroll_internal_salary,
            })
        return res

    def action_apply(self):
        self.ensure_one()
        self.line_id.write({'payroll_internal_salary': self.new_lnb})
        return {'type': 'ir.actions.act_window_close'}
