# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SalaryKpiExportWizard(models.TransientModel):
    _name = 'dl.salary.kpi.export.wizard'
    _description = 'Wizard Xuất báo cáo Excel'

    month_id = fields.Many2one('dl.salary.kpi.month', string='Tháng lương', required=True)
    salary_attachment_id = fields.Many2one('ir.attachment', string='File Báo cáo Lương')
    kpi_attachment_id = fields.Many2one('ir.attachment', string='File Báo cáo KPI')

    def action_export_salary(self):
        """Tải file báo cáo lương từ background thread."""
        self.ensure_one()
        if not self.salary_attachment_id or not self.salary_attachment_id.datas:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Chờ chút...'),
                    'message': _('Báo cáo đang được xử lý ngầm, vui lòng nhấn lại sau 10-20 giây.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
            
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.salary_attachment_id.id}?download=true',
            'target': 'new',
        }

    def action_export_kpi_point(self):
        """Tải file báo cáo KPI từ background thread."""
        self.ensure_one()
        if not self.kpi_attachment_id or not self.kpi_attachment_id.datas:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Chờ chút...'),
                    'message': _('Báo cáo đang được xử lý ngầm, vui lòng nhấn lại sau 10-20 giây.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.kpi_attachment_id.id}?download=true',
            'target': 'new',
        }
