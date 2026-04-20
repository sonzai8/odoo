# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import os
import werkzeug

class SalaryKpiController(http.Controller):
    @http.route('/dl_salary_kpi/download_template', type='http', auth='user')
    def download_template(self, filename=None, **kwargs):
        # Get the path to the static template
        # Absolute path relative to this file
        current_dir = os.path.dirname(__file__)
        addon_dir = os.path.dirname(current_dir)
        template_path = os.path.join(addon_dir, 'static', 'xlsx', 'TEMPLATE_DL_SALARY_KPI.xlsx')
        
        if not os.path.exists(template_path):
            return request.not_found()
            
        with open(template_path, 'rb') as f:
            content = f.read()
            
        # Use filename from params or default
        download_name = filename or 'TEMPLATE_DL_SALARY_KPI.xlsx'
        
        # In Odoo, content_disposition handles the filename header
        headers = [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', http.content_disposition(download_name)),
        ]
        return request.make_response(content, headers)

    @http.route('/dl_salary_kpi/export_month/<int:month_id>', type='http', auth='user')
    def export_month(self, month_id, **kwargs):
        import logging
        _logger = logging.getLogger(__name__)
        try:
            month = request.env['dl.salary.kpi.month'].browse(month_id)
            if not month.exists():
                return request.not_found()
                
            content = month._generate_excel_report()
            
            month_str = month.date_month.strftime('%m-%Y') if month.date_month else 'BC'
            filename = f"Báo Cáo Lương Tháng {month_str}.xlsx"
            
            headers = [
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', http.content_disposition(filename)),
            ]
            return request.make_response(content, headers)
        except Exception as e:
            _logger.exception("EXPORT CONTROLLER ERROR")
            # Return a user-friendly error message instead of a generic 500
            error_msg = f"""
                <html>
                    <body style="font-family: sans-serif; padding: 50px; text-align: center;">
                        <h2 style="color: #d9534f;">Lỗi khi xuất báo cáo Excel</h2>
                        <div style="background: #f9f9f9; padding: 20px; border: 1px solid #ddd; margin: 20px auto; max-width: 600px; text-align: left;">
                            <strong>Chi tiết lỗi:</strong> <pre style="white-space: pre-wrap;">{str(e)}</pre>
                        </div>
                        <p>Vui lòng kiểm tra lại dữ liệu hoặc liên hệ kỹ thuật để được hỗ trợ.</p>
                        <button onclick="window.history.back()" style="padding: 10px 20px; cursor: pointer;">Quay lại</button>
                    </body>
                </html>
            """
            return request.make_response(error_msg, status=200)
