# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SalaryKpiExportWizard(models.TransientModel):
    _name = 'dl.salary.kpi.export.wizard'
    _description = 'Wizard Xuất báo cáo Excel'

    month_id = fields.Many2one('dl.salary.kpi.month', string='Tháng lương', required=True)

    def action_export_salary(self):
        """Xuất báo cáo lương tổng hợp."""
        self.ensure_one()
        return self.month_id.action_export_salary_report()

    def action_export_kpi_point(self):
        """Xuất báo cáo điểm KPI theo bộ phận."""
        self.ensure_one()
        return self.month_id.action_export_kpi_point_report()
