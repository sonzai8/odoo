# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import io
import openpyxl
from datetime import datetime, date

class SalaryKpiTaxImport(models.TransientModel):
    _name = 'dl.salary.kpi.tax.import'
    _description = 'Wizard nhập thông tin thuế nhân viên'

    file_data = fields.Binary(string='File Excel')
    file_name = fields.Char(string='Tên file')
    state = fields.Selection([('init', 'Chọn File'), ('preview', 'Xem trước')], default='init')
    preview_html = fields.Html(string='Xem trước dữ liệu')

    def action_export_template(self):
        """Xuất file mẫu chứa danh sách nhân viên hiện có"""
        return {
            'type': 'ir.actions.act_url',
            'url': '/dl_salary_kpi/export_tax_employees',
            'target': 'new',
        }

    def _parse_date(self, value):
        if not value:
            return False
        if isinstance(value, (date, datetime)):
            return value
        if isinstance(value, str):
            value = value.strip()
            for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y'):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        return False

    def _read_excel_data(self):
        if not self.file_data:
            raise UserError("Vui lòng chọn file Excel trước khi thực hiện.")
        
        file_content = base64.b64decode(self.file_data)
        wb = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
        ws = wb.active

        parsed_data = []
        # Bắt đầu đọc từ dòng 2
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
            if not row or not any(row[1:3]): # Kiểm tra có dữ liệu cơ bản không
                continue
            
            # Cấu trúc: 0:STT, 1:ID NV, 2:Họ tên, 3:Tên riêng, 4:CCCD, 5:Ngày sinh, 6:Email, 7:SĐT, 8:Giới tính, 9:MST, 10:Chức vụ, 11:Phòng ban, 12:Lương, 13:Ngày nghỉ
            emp_id = int(row[1]) if row[1] and str(row[1]).isdigit() else False
            name = str(row[2]).strip() if row[2] else ''
            dl_tax_id = str(row[9]).strip() if len(row) > 9 and row[9] else ''
            dept_name = str(row[11]).strip() if len(row) > 11 and row[11] else ''
            
            error = ""
            if not name:
                error = "Thiếu Họ và tên."
            elif not dl_tax_id:
                error = "Thiếu Mã số thuế."
            
            employee = False
            if emp_id:
                employee = self.env['hr.employee'].browse(emp_id)
                if not employee.exists():
                    employee = False
            
            if not employee and name and dl_tax_id:
                employee = self.env['hr.employee'].search([('name', '=', name), ('dl_tax_id', '=', dl_tax_id)], limit=1)

            parsed_data.append({
                'row_idx': row_idx,
                'emp_id': emp_id,
                'name': name,
                'dl_first_name': str(row[3]) if len(row) > 3 and row[3] else '',
                'identification_id': str(row[4]) if len(row) > 4 and row[4] else '',
                'birthday': self._parse_date(row[5]) if len(row) > 5 else False,
                'email': str(row[6]) if len(row) > 6 and row[6] else '',
                'work_phone': str(row[7]) if len(row) > 7 and row[7] else '',
                'sex': str(row[8]) if len(row) > 8 and row[8] else '',
                'dl_tax_id': dl_tax_id,
                'dl_tax_position': str(row[10]) if len(row) > 10 and row[10] else '',
                'dl_tax_department_name': dept_name,
                'dl_tax_base_salary': float(row[12]) if len(row) > 12 and row[12] else 0.0,
                'dl_departure_date': self._parse_date(row[13]) if len(row) > 13 else False,
                'error': error
            })
        return parsed_data

    def action_preview(self):
        parsed_data = self._read_excel_data()
        if not parsed_data:
            raise UserError("File Excel không có dữ liệu hợp lệ.")

        valid_count = sum(1 for d in parsed_data if not d['error'])
        error_count = len(parsed_data) - valid_count

        preview_rows = parsed_data[:5]
        if len(parsed_data) > 10:
            preview_rows.extend([None])
            preview_rows.extend(parsed_data[-5:])
        elif len(parsed_data) > 5:
            preview_rows.extend(parsed_data[5:])

        html = f"""
        <div class="alert alert-info">
            <strong>Tổng số nhân viên trong file:</strong> {len(parsed_data)}<br/>
            <strong>Hợp lệ:</strong> <span class="text-success">{valid_count}</span> | 
            <strong>Lỗi:</strong> <span class="text-danger">{error_count}</span>
        </div>
        <table class="table table-sm table-bordered">
            <thead class="table-light">
                <tr>
                    <th>Dòng</th>
                    <th>ID NV</th>
                    <th>Họ và tên</th>
                    <th>Mã số thuế</th>
                    <th>CCCD</th>
                    <th>Phòng ban thuế</th>
                    <th>Lương thuế</th>
                    <th>Trạng thái</th>
                </tr>
            </thead>
            <tbody>
        """

        for row in preview_rows:
            if row is None:
                html += """<tr><td colspan="8" class="text-center"><strong>...</strong></td></tr>"""
                continue
            
            row_class = "table-danger" if row['error'] else ""
            status_text = f"<span class='text-danger'>{row['error']}</span>" if row['error'] else "<span class='text-success'>Hợp lệ</span>"
            
            html += f"""
                <tr class="{row_class}">
                    <td>{row['row_idx']}</td>
                    <td>{row['emp_id'] or ''}</td>
                    <td>{row['name']}</td>
                    <td>{row['dl_tax_id']}</td>
                    <td>{row['identification_id']}</td>
                    <td>{row['dl_tax_department_name']}</td>
                    <td>{row['dl_tax_base_salary']:,.0f}</td>
                    <td>{status_text}</td>
                </tr>
            """
        html += "</tbody></table>"

        self.preview_html = html
        self.state = 'preview'
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dl.salary.kpi.tax.import',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_back(self):
        self.state = 'init'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dl.salary.kpi.tax.import',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_confirm_import(self):
        parsed_data = self._read_excel_data()
        
        count_create = 0
        count_update = 0
        
        # Cache phòng ban để tối ưu
        dept_cache = {d.name: d.id for d in self.env['dl.tax.department'].search([])}

        for row in parsed_data:
            if row['error']:
                continue

            dept_id = dept_cache.get(row['dl_tax_department_name'])

            vals = {
                'name': row['name'],
                'birthday': row['birthday'],
                'dl_first_name': row['dl_first_name'],
                'email': row['email'],
                'work_phone': row['work_phone'],
                'identification_id': row['identification_id'],
                'sex': 'male' if str(row['sex'] or '').strip().upper() == 'NAM' else 'female' if str(row['sex'] or '').strip().upper() == 'NỮ' else 'other',
                'dl_tax_id': row['dl_tax_id'],
                'dl_tax_position': row['dl_tax_position'],
                'dl_tax_department_id': dept_id,
                'dl_tax_base_salary': row['dl_tax_base_salary'],
                'dl_departure_date': row['dl_departure_date'],
            }
            
            employee = False
            if row['emp_id']:
                employee = self.env['hr.employee'].browse(row['emp_id'])
                if not employee.exists():
                    employee = False
            
            if not employee and row['name'] and row['dl_tax_id']:
                employee = self.env['hr.employee'].search([('name', '=', row['name']), ('dl_tax_id', '=', row['dl_tax_id'])], limit=1)

            if employee:
                employee.write(vals)
                count_update += 1
            else:
                self.env['hr.employee'].create(vals)
                count_create += 1
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành công'),
                'message': _('Đã xử lý xong: %s cập nhật, %s thêm mới.') % (count_update, count_create),
                'type': 'success',
                'sticky': False,
            }
        }
