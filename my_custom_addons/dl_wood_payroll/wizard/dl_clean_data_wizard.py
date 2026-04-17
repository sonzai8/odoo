# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import calendar
from datetime import date

class DLCleanDataWizard(models.TransientModel):
    _name = 'dl.clean.data.wizard'
    _description = 'Tiện ích xóa dữ liệu rác'

    year = fields.Integer(string='Năm', default=lambda self: date.today().year, required=True)
    month = fields.Selection([
        ('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'), ('4', 'Tháng 4'),
        ('5', 'Tháng 5'), ('6', 'Tháng 6'), ('7', 'Tháng 7'), ('8', 'Tháng 8'),
        ('9', 'Tháng 9'), ('10', 'Tháng 10'), ('11', 'Tháng 11'), ('12', 'Tháng 12'),
    ], string='Tháng', default=lambda self: str(date.today().month), required=True)

    def action_clean_data(self):
        self.ensure_one()
        
        # Build date range
        month_int = int(self.month)
        last_day = calendar.monthrange(self.year, month_int)[1]
        start_date = date(self.year, month_int, 1)
        end_date = date(self.year, month_int, last_day)

        # 1. Delete Combined Logs (and its lines via O2M cascade)
        # We search with sudo to bypass record rules if any
        combined_logs = self.env['dl.combined.log'].sudo().search([
            ('date', '>=', start_date),
            ('date', '<=', end_date)
        ])
        log_count = len(combined_logs)
        combined_logs.unlink()

        # 2. Delete Daily Attendance
        attendances = self.env['dl.daily.attendance'].sudo().search([
            ('date', '>=', start_date),
            ('date', '<=', end_date)
        ])
        att_count = len(attendances)
        attendances.unlink()

        # 3. Delete Production Logs
        production_logs = self.env['dl.production.log'].sudo().search([
            ('date', '>=', start_date),
            ('date', '<=', end_date)
        ])
        prod_count = len(production_logs)
        production_logs.unlink()

        # 4. Delete Pooling Results
        pooling_results = self.env['dl.daily.pooling.result'].sudo().search([
            ('date', '>=', start_date),
            ('date', '<=', end_date)
        ])
        pool_count = len(pooling_results)
        pooling_results.unlink()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành công'),
                'message': _('Đã xóa sạch dữ liệu tháng %s/%s: %d Phiếu kết hợp, %d Chấm công, %d Sản lượng, %d Kết quả cào bằng.') % (
                    self.month, self.year, log_count, att_count, prod_count, pool_count
                ),
                'sticky': False,
                'type': 'success',
            }
        }
