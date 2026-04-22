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
    file_data = fields.Binary(string='File Excel', required=True)
    file_name = fields.Char(string='Tên file')

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

            vals = {}
            row_codes = {} # To check shift change
            
            # Lấy dữ liệu hiện tại từ hệ thống để so sánh chuỗi
            for day in range(1, 32):
                field_name = f'day_{day:02d}'
                current_att = getattr(line, field_name)
                row_codes[day] = current_att.code if current_att else False

            # Ghi đè bằng dữ liệu từ Excel
            for day in range(1, 32):
                code = str(row[4 + day - 1]).strip().upper() if row[4 + day - 1] else ""
                if code:
                    if code not in att_type_map:
                        errors.append(f"Dòng {row_idx}: Mã công '{code}' ngày {day:02d} không hợp lệ.")
                    else:
                        vals[f'day_{day:02d}'] = att_type_map[code]
                        row_codes[day] = code
                else:
                    vals[f'day_{day:02d}'] = False
                    row_codes[day] = False

            # Kiểm tra quy tắc đổi ca ngay tại đây để gom lỗi
            for i in range(1, 31):
                cur = row_codes.get(i)
                nxt = row_codes.get(i+1)
                if cur == 'N' and nxt == 'Đ':
                    errors.append(f"Dòng {row_idx} ({emp_name}): Lỗi đổi ca N sang Đ tại ngày {i:02d}-{i+1:02d} (Thiếu ĐC).")

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

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành công'),
                'message': _('Đã cập nhật dữ liệu cho %s nhân viên.') % len(import_data),
                'type': 'success',
            }
        }
