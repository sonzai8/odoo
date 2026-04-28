# -*- coding: utf-8 -*-
import base64
import os
import io
import datetime
from odoo import models, fields, api, _
from odoo.tools import file_path

try:
    from openpyxl import load_workbook
except ImportError:
    load_workbook = None

class SalaryKpiExportWizard(models.TransientModel):
    _name = 'dl.salary.kpi.export.wizard'
    _description = 'Xuất bảng lương & KPI Excel'

    month_id = fields.Many2one('dl.salary.kpi.month', string='Tháng lương', required=True)

    def action_export_xlsx(self):
        if not load_workbook:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Lỗi'),
                    'message': _('Thư viện openpyxl chưa được cài đặt.'),
                    'type': 'danger',
                }
            }

        # 1. Lấy template
        try:
            template_path = file_path('dl_salary_kpi/static/xlsx/TEMPLATE_DL_SALARY_KPI.xlsx')
        except FileNotFoundError:
            template_path = False

        if not template_path:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Lỗi'),
                    'message': _('Không tìm thấy file mẫu Excel tại static/xlsx/TEMPLATE_DL_SALARY_KPI.xlsx'),
                    'type': 'danger',
                }
            }

        # 2. Đọc và điền dữ liệu
        wb = load_workbook(template_path)
        ws = wb.active

        # Giả sử template có các ô tiêu đề:
        # C3: Tháng/Năm
        # C4: Doanh thu công ty
        ws['C3'] = self.month_id.date_month.strftime('%m/%Y') if self.month_id.date_month else ''
        ws['C4'] = self.month_id.company_revenue

        # Giả sử danh sách nhân viên bắt đầu từ dòng 7
        row = 7
        for line in self.month_id.line_ids:
            ws.cell(row=row, column=1, value=line.employee_id.name)
            ws.cell(row=row, column=2, value=line.employee_id.department_id.name if line.employee_id.department_id else '')
            ws.cell(row=row, column=3, value=line.allowance_amount)
            ws.cell(row=row, column=4, value=line.bonus_amount)
            ws.cell(row=row, column=5, value=line.kpi_score)
            ws.cell(row=row, column=6, value=line.total_salary_balance)
            row += 1

        # 3. Xuất file
        output = io.BytesIO()
        wb.save(output)
        file_data = base64.b64encode(output.getvalue())
        output.close()

        # Định dạng tên file: DL_Bang_Luong_Thang_{Month}_2026
        month_str = self.month_id.date_month.strftime('%m') if self.month_id.date_month else '00'
        year_str = self.month_id.date_month.strftime('%Y') if self.month_id.date_month else '2026'
        filename = f"DL_Bang_Luong_Thang_{month_str}_{year_str}.xlsx"

        # 4. Trả về file download
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': file_data,
            'store_fname': filename,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
