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
    
    line_ids = fields.One2many('dl.salary.kpi.tax.import.line', 'import_id', string='Chi tiết xem trước')
    state = fields.Selection([
        ('upload', 'Tải lên'),
        ('verify', 'Kiểm tra')
    ], default='upload')

    total_records = fields.Integer(string='Tổng số bản ghi')
    error_summary = fields.Text(string='Tóm tắt lỗi')
    has_errors = fields.Boolean(string='Có lỗi', default=False)

    def action_export_template(self):
        """Xuất file mẫu chứa danh sách nhân viên hiện có"""
        return {
            'type': 'ir.actions.act_url',
            'url': '/dl_salary_kpi/export_tax_employees',
            'target': 'new',
        }

    def _parse_date(self, value):
        """Hàm bổ trợ để phân tích ngày tháng từ Excel (hỗ trợ cả datetime và string)"""
        if not value:
            return False
        if isinstance(value, (date, datetime)):
            return value
        
        # Nếu là string, thử parse theo các định dạng phổ biến
        if isinstance(value, str):
            value = value.strip()
            for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y'):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        return False

    def action_verify(self):
        """Đọc file và hiển thị bản xem trước để người dùng kiểm tra"""
        if not self.file_data:
            raise UserError("Vui lòng chọn file Excel trước khi kiểm tra.")
        
        file_content = base64.b64decode(self.file_data)
        wb = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
        ws = wb.active

        # 1. Kiểm tra Template (Header)
        expected_headers = [
            "STT", "ID NV", "Họ và tên", "Tên riêng", "Số CCCD", "Ngày sinh", "Email", "SĐT", 
            "Giới tính", "Mã số thuế", "Chức vụ thuế", 
            "Phòng ban thuế", "Lương cơ bản thuế", "Ngày nghỉ việc"
        ]
        
        # Đọc dòng đầu tiên để so khớp header
        actual_headers = [str(cell.value).strip() if cell.value else "" for cell in ws[1]]
        
        # Kiểm tra linh hoạt: Ít nhất phải có ID NV hoặc Mã số thuế ở các cột tương ứng
        if len(actual_headers) < 11:
            raise UserError(_("File Excel không đúng định dạng mẫu (thiếu cột). Vui lòng sử dụng file mẫu từ hệ thống."))

        # Kiểm tra cụ thể ID NV (Cột B) và Mã số thuế (Cột J)
        if actual_headers[1].upper() != "ID NV" and actual_headers[9].upper() != "MÃ SỐ THUẾ":
             raise UserError(_("Cấu trúc file không khớp. Cột B phải là 'ID NV' hoặc Cột J phải là 'Mã số thuế'.\n"
                               "Hiện tại: Cột B='%s', Cột J='%s'") % (actual_headers[1], actual_headers[9]))

        self.line_ids.unlink()
        new_lines = []
        all_rows = list(ws.iter_rows(min_row=2, values_only=True))
        valid_rows = []
        
        # 1. Lọc các dòng có dữ liệu
        for row in all_rows:
            if not row or len(row) < 3:
                continue
            if not any(val is not None for val in row[1:]):
                continue
            valid_rows.append(row)

        total_valid = len(valid_rows)
        errors = []
        
        # 2. Xử lý bản ghi để hiển thị preview (5 đầu, 5 cuối)
        indices_to_show = set()
        if total_valid <= 10:
            indices_to_show = set(range(total_valid))
        else:
            indices_to_show = set(range(5)) | set(range(total_valid - 5, total_valid))

        for idx, row in enumerate(valid_rows):
            try:
                emp_id = int(row[1]) if row[1] else False
            except (ValueError, TypeError):
                emp_id = False

            name = str(row[2]) if row[2] else ''
            dl_tax_id = str(row[9]) if len(row) > 9 and row[9] else ''
            
            error_msg = ""
            if not name:
                error_msg = "Dòng thiếu thông tin Họ tên để xác định nhân viên."
            
            # Kiểm tra phòng ban
            dept_name = str(row[11]).strip() if len(row) > 11 and row[11] else ''
            if dept_name:
                tax_dept = self.env['dl.tax.department'].search([('name', '=', dept_name)], limit=1)
                if not tax_dept:
                    error_msg = f"Phòng ban thuế '{dept_name}' không tồn tại."

            if error_msg:
                errors.append(f"Dòng {idx + 2}: {error_msg}")

            # Chỉ tạo line nếu nằm trong danh sách preview
            if idx in indices_to_show:
                import_type = 'insert'
                if emp_id:
                    employee = self.env['hr.employee'].browse(emp_id)
                    if employee.exists():
                        import_type = 'update'
                elif name and dl_tax_id:
                    employee = self.env['hr.employee'].search([('name', '=', name), ('dl_tax_id', '=', dl_tax_id)], limit=1)
                    if employee:
                        import_type = 'update'
                        emp_id = employee.id

                new_lines.append((0, 0, {
                    'employee_id': emp_id,
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
                    'import_type': import_type,
                    'error_msg': error_msg,
                }))
            
        # Hiển thị tối đa 10 lỗi trong summary để tránh quá tải
        summary = ""
        if errors:
            summary = "Tìm thấy lỗi trong file:\n" + "\n".join(errors[:10])
            if len(errors) > 10:
                summary += f"\n... và {len(errors) - 10} lỗi khác."

        self.write({
            'line_ids': new_lines,
            'state': 'verify',
            'total_records': total_valid,
            'error_summary': summary,
            'has_errors': len(errors) > 0
        })
        
        return {
            'name': 'Kiểm tra thông tin nhập (Chế độ Xem trước)',
            'type': 'ir.actions.act_window',
            'res_model': 'dl.salary.kpi.tax.import',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_confirm_import(self):
        """Xác nhận cập nhật dữ liệu chính thức - Thực hiện parse lại toàn bộ file"""
        self.ensure_one()
        if self.has_errors:
            raise UserError("Vui lòng xử lý hết các lỗi trong file trước khi xác nhận.")
            
        if not self.file_data:
            raise UserError("File dữ liệu không còn tồn tại.")

        file_content = base64.b64decode(self.file_data)
        wb = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
        ws = wb.active
        
        count_create = 0
        count_update = 0
        
        # Cache phòng ban để tối ưu
        dept_cache = {d.name: d.id for d in self.env['dl.tax.department'].search([])}

        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or len(row) < 3:
                continue
            if not any(val is not None for val in row[1:]):
                continue
            
            try:
                emp_id = int(row[1]) if row[1] else False
            except (ValueError, TypeError):
                emp_id = False

            name = str(row[2]) if row[2] else ''
            dl_tax_id = str(row[9]) if len(row) > 9 and row[9] else ''
            dept_name = str(row[11]).strip() if len(row) > 11 and row[11] else ''
            dept_id = dept_cache.get(dept_name)

            vals = {
                'name': name,
                'birthday': self._parse_date(row[5]) if len(row) > 5 else False,
                'dl_first_name': str(row[3]) if len(row) > 3 and row[3] else '',
                'email': str(row[6]) if len(row) > 6 and row[6] else '',
                'work_phone': str(row[7]) if len(row) > 7 and row[7] else '',
                'identification_id': str(row[4]) if len(row) > 4 and row[4] else '',
                'sex': 'male' if str(row[8] or '').strip().upper() == 'NAM' else 'female' if str(row[8] or '').strip().upper() == 'NỮ' else 'other',
                'dl_tax_id': dl_tax_id,
                'dl_tax_position': str(row[10]) if len(row) > 10 and row[10] else '',
                'dl_tax_department_id': dept_id,
                'dl_tax_base_salary': float(row[12]) if len(row) > 12 and row[12] else 0.0,
                'dl_departure_date': self._parse_date(row[13]) if len(row) > 13 else False,
            }
            
            # Tìm kiếm nhân viên để cập nhật hoặc tạo mới
            employee = False
            if emp_id:
                employee = self.env['hr.employee'].browse(emp_id)
                if not employee.exists():
                    employee = False
            
            if not employee and name and dl_tax_id:
                employee = self.env['hr.employee'].search([('name', '=', name), ('dl_tax_id', '=', dl_tax_id)], limit=1)

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

class SalaryKpiTaxImportLine(models.TransientModel):
    _name = 'dl.salary.kpi.tax.import.line'
    _description = 'Dòng xem trước nhập thuế'

    import_id = fields.Many2one('dl.salary.kpi.tax.import', ondelete='cascade')
    employee_id = fields.Integer(string='ID NV')
    name = fields.Char(string='Họ và tên')
    birthday = fields.Date(string='Ngày sinh')
    dl_first_name = fields.Char(string='Tên riêng')
    email = fields.Char(string='Email')
    work_phone = fields.Char(string='SĐT')
    identification_id = fields.Char(string='Số CCCD')
    sex = fields.Char(string='Giới tính')
    dl_tax_id = fields.Char(string='Mã số thuế')
    dl_tax_position = fields.Char(string='Chức vụ thuế')
    dl_tax_department_name = fields.Char(string='Phòng ban thuế')
    dl_tax_base_salary = fields.Float(string='Lương thuế')
    dl_departure_date = fields.Date(string='Ngày nghỉ việc')
    
    import_type = fields.Selection([
        ('insert', 'Thêm mới'),
        ('update', 'Cập nhật')
    ], string='Loại hành động')
    
    error_msg = fields.Char(string='Lỗi', readonly=True)
