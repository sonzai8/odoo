# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64
import io
import openpyxl

class SalaryKpiImportWizard(models.TransientModel):
    _name = 'dl.salary.kpi.import.wizard'
    _description = 'Wizard nhập bảng công'

    month_id = fields.Many2one('dl.salary.kpi.month', string='Tháng bảng công')
    wizard_type = fields.Selection([
        ('normal', 'Công Thường'),
        ('overtime', 'Làm Thêm')
    ], string='Loại xử lý', default='normal')
    file_data = fields.Binary(string='File Excel', required=False)
    file_name = fields.Char(string='Tên file')

    def action_export(self):
        self.ensure_one()
        if self.wizard_type == 'overtime':
            return self.month_id.action_export_ot_excel()
        return self.month_id.action_export_excel()

    def action_import(self):
        if not self.file_data:
            return
        
        file_content = base64.b64decode(self.file_data)
        wb = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
        ws = wb.active

        # Lấy bản đồ mã công -> ID
        att_types = self.env['dl.salary.kpi.attendance.type'].search([])
        att_type_map = {t.code: t.id for t in att_types}
        att_code_map = {t.id: t.code for t in att_types}

        errors = []
        import_data = [] # List of (line_record, values_to_write)

        # Duyệt từ dòng 4 (skip headers)
        count_skipped_departure = 0
        from datetime import date

        for row_idx, row in enumerate(ws.iter_rows(min_row=4, values_only=True), 4):

            if not row[2]: # Cột C là ID nhân viên
                continue
            
            emp_name = str(row[1]) if row[1] else ""
            emp_id = int(row[2])
            
            # Tìm line tương ứng trong tháng
            line = self.month_id.line_ids.filtered(lambda l: l.employee_id.id == emp_id)
            if not line:
                errors.append(f"Dòng {row_idx}: Không tìm thấy nhân viên ID {emp_id} trong bảng công này.")
                continue
            
            if line.employee_id.name != emp_name:
                errors.append(f"Dòng {row_idx}: Tên nhân viên không khớp (Hệ thống: {line.employee_id.name}, Excel: {emp_name}).")
                continue

            # Kiểm tra ngày nghỉ việc
            departure_date = line.employee_id.dl_departure_date
            month_date = self.month_id.date_month
            year, month = month_date.year, month_date.month

            vals = {}
            row_codes = {} # To check shift change
            has_departure_skip = False
            
            # Lấy dữ liệu hiện tại từ hệ thống để so sánh chuỗi
            for day in range(1, 32):
                field_name = f'day_{i:02d}' if self.wizard_type == 'normal' else f'ot_day_{i:02d}'
                # Note: 'i' is not defined here, should be 'day'
                field_name = f'day_{day:02d}' if self.wizard_type == 'normal' else f'ot_day_{day:02d}'
                current_att = getattr(line, field_name)
                row_codes[day] = current_att.code if current_att else False

            # Ghi đè bằng dữ liệu từ Excel
            col_offset = 4 if self.wizard_type == 'normal' else 40
            for day in range(1, 32):
                field_name = f'day_{day:02d}' if self.wizard_type == 'normal' else f'ot_day_{day:02d}'
                
                # Check departure date
                try:
                    d = date(year, month, day)
                    if departure_date and d > departure_date:
                        vals[field_name] = False
                        row_codes[day] = False
                        has_departure_skip = True
                        continue
                except ValueError:
                    pass

                # Excel index: col_offset + day - 1
                try:
                    val = row[col_offset + day - 1]
                    code = str(val).strip().upper() if val else ""
                except IndexError:
                    code = ""

                if code:
                    if code not in att_type_map:
                        errors.append(f"Dòng {row_idx}: Mã công '{code}' ngày {day:02d} không hợp lệ.")
                    else:
                        vals[field_name] = att_type_map[code]
                        row_codes[day] = code
                else:
                    vals[field_name] = False
                    row_codes[day] = False

            if has_departure_skip:
                count_skipped_departure += 1

            # Kiểm tra quy tắc đổi ca (chỉ cho công thường)
            if self.wizard_type == 'normal':
                for i in range(1, 31):
                    cur = row_codes.get(i)
                    nxt = row_codes.get(i+1)
                    if cur == 'Đ' and nxt == 'N':
                        errors.append(f"Dòng {row_idx} ({emp_name}): Lỗi đổi ca Đ sang N tại ngày {i:02d}-{i+1:02d} (Thiếu ĐC).")

            if vals and not errors:
                import_data.append((line, vals))

        if errors:
            # Chỉ hiển thị tối đa 10 lỗi đầu tiên
            display_errors = errors[:10]
            if len(errors) > 10:
                display_errors.append(f"... và còn {len(errors) - 10} lỗi khác nữa.")
            raise UserError("\n".join(display_errors))

        # Nếu không có lỗi nào thì mới tiến hành lưu
        for line, vals in import_data:
            line.write(vals)

        msg = _('Đã cập nhật dữ liệu cho %s nhân viên.') % len(import_data)
        if count_skipped_departure > 0:
            msg += _('\nLưu ý: Có %s nhân viên bị bỏ qua các ngày sau ngày nghỉ việc.') % count_skipped_departure

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành công'),
                'message': msg,
                'type': 'success',
                'sticky': True if count_skipped_departure > 0 else False,
            }
        }
