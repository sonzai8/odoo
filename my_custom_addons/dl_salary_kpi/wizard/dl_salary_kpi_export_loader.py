# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SalaryKpiExportLoading(models.TransientModel):
    _name = 'dl.salary.kpi.export.loading'
    _description = 'Thông báo đang xuất báo cáo'

    month_id = fields.Many2one('dl.salary.kpi.month', string='Tháng')

    def action_download(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/dl_salary_kpi/export_month/{self.month_id.id}',
            'target': 'self',
        }
