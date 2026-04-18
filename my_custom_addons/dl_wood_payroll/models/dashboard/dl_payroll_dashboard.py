# -*- coding: utf-8 -*-
"""
TransientModel cho Dashboard KPI.
Pattern: mỗi record = 1 stat box trên kanban view.
Dùng widget="statinfo" để hiển thị KPI name + value.
"""
from odoo import models, fields, api
from datetime import date
import calendar


class PayrollDashboard(models.TransientModel):
    _name = 'dl.payroll.dashboard'
    _description = 'Dashboard KPI Payroll'
    _order = 'sequence'

    name = fields.Char(string='Label', required=True)
    sequence = fields.Integer(default=10)

    # Các trường cho stat box
    stat_value = fields.Char(
        string='Stat Value',
        help='Giá trị hiển thị bên trong stat box (số lớn ở giữa)'
    )
    stat_label = fields.Char(
        string='Stat Label',
        help='Dòng mô tả nhỏ bên dưới'
    )
    action_id = fields.Many2one(
        'ir.actions.act_window',
        string='Action',
        help='Click vào stat box sẽ nhảy đến action này'
    )
    icon = fields.Char(string='Icon Class', default='fa fa-line-chart')
    bg_color = fields.Char(string='Background Color', default='#0073aa')

    def _reload_with_kpis(self):
        """Xóa records cũ, tạo 6 KPI records mới, reload view."""
        self._create_kpi_records()
        return self._reopen_view()

    def _reopen_view(self):
        """Mở lại kanban view của chính model này."""
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'kanban',
            'target': 'current',
        }

    @api.model
    def _create_kpi_records(self):
        """Compute KPIs và tạo records cho tháng hiện tại."""
        today = date.today()
        year, month = today.year, today.month
        month_name = calendar.month_name[month]

        first_day = date(year, month, 1)
        _, last_day_num = calendar.monthrange(year, month)
        last_day = date(year, month, last_day_num)

        # 1. Pooling data
        pooling = self.env['dl.daily.pooling.result'].read_group(
            [('date', '>=', first_day), ('date', '<=', last_day)],
            ['actual_work_days', 'final_salary', 'contribution_amount'],
            []
        )
        total_work = pooling[0]['actual_work_days'] if pooling else 0
        total_salary = pooling[0]['final_salary'] if pooling else 0
        total_yield = pooling[0]['contribution_amount'] if pooling else 0

        # 2. Confirmed days
        confirmed_days = self.env['dl.daily.pooling.result'].search_count([
            ('date', '>=', first_day), ('date', '<=', last_day),
        ])

        # 3. Active employees
        emp_ids = self.env['dl.daily.attendance.line'].search([
            ('date', '>=', first_day), ('date', '<=', last_day),
        ]).mapped('employee_id.id')
        active_employees = len(set(emp_ids))

        # 4. Total fines
        fines = self.env['dl.employee.fine'].read_group([
            ('date', '>=', first_day), ('date', '<=', last_day),
        ], ['amount'], [])
        total_fines = fines[0]['amount'] if fines else 0

        # Remove old records
        self.search([]).unlink()

        # Lookup action ids
        action_combined = self.env.ref('dl_wood_payroll.action_dl_combined_log', False)
        action_pooling_result = self.env.ref('dl_wood_payroll.action_dl_daily_pooling_result', False)
        action_fine = self.env.ref('dl_wood_payroll.action_dl_employee_fine', False)
        action_attendance = self.env.ref('dl_wood_payroll.action_dl_daily_attendance', False)

        def fmt(val):
            return '{:,.0f}'.format(int(val)).replace(',', '.')

        # Create KPI records
        kpis = [
            {
                'name': 'Tổng số công',
                'sequence': 10,
                'stat_value': str(round(total_work, 1)),
                'stat_label': f'{month_name} {year}',
                'icon': 'fa fa-clock-o',
                'bg_color': '#0073aa',
                'action_id': action_attendance.id if action_attendance else False,
            },
            {
                'name': 'Tổng quỹ lương',
                'sequence': 20,
                'stat_value': fmt(total_salary),
                'stat_label': f'{month_name} {year} — VNĐ',
                'icon': 'fa fa-money',
                'bg_color': '#28a745',
                'action_id': action_combined.id if action_combined else False,
            },
            {
                'name': 'Tổng sản lượng',
                'sequence': 30,
                'stat_value': fmt(total_yield),
                'stat_label': f'{month_name} {year}',
                'icon': 'fa fa-database',
                'bg_color': '#17a2b8',
                'action_id': action_pooling_result.id if action_pooling_result else False,
            },
            {
                'name': 'NV có mặt tháng',
                'sequence': 40,
                'stat_value': str(active_employees),
                'stat_label': f'{month_name} {year}',
                'icon': 'fa fa-users',
                'bg_color': '#8e44ad',
                'action_id': False,
            },
            {
                'name': 'Ngày đã cào bằng',
                'sequence': 50,
                'stat_value': str(confirmed_days),
                'stat_label': f'/{last_day_num} ngày — {month_name} {year}',
                'icon': 'fa fa-check-circle-o',
                'bg_color': '#e67e22',
                'action_id': action_pooling_result.id if action_pooling_result else False,
            },
            {
                'name': 'Tổng phạt tháng',
                'sequence': 60,
                'stat_value': fmt(total_fines),
                'stat_label': f'{month_name} {year} — VNĐ',
                'icon': 'fa fa-warning',
                'bg_color': '#dc3545',
                'action_id': action_fine.id if action_fine else False,
            },
        ]

        self.create(kpis)

    @api.model
    def action_open_dashboard(self):
        """Được gọi từ menu — tạo KPI records rồi mở kanban view."""
        self._create_kpi_records()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tổng quan Lương & Sản lượng',
            'res_model': self._name,
            'view_mode': 'kanban',
            'target': 'main',
        }
