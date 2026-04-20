from odoo import models, fields

class SalaryKpiNotice(models.Model):
    _name = 'dl.salary.kpi.notice'
    _description = 'KPI Calculation Notice'

    name = fields.Char(string='Tiêu đề', default='Tính năng đang phát triển')
    message = fields.Html(string='Thông báo', default="""
        <div class="alert alert-info" role="alert" style="margin-top: 20px; font-size: 18px;">
            <i class="fa fa-info-circle"></i> Đang xây dựng tính năng tính năng KPI cho nhân viên.
        </div>
    """)
