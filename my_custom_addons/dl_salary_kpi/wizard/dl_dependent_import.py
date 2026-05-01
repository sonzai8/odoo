# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import io
import openpyxl
from datetime import datetime, date

class DLDependentImport(models.TransientModel):
    _name = 'dl.dependent.import'
    _description = 'Nhập người phụ thuộc từ Excel'

    file_data = fields.Binary(string='File Excel')
    file_name = fields.Char(string='Tên file')

    state = fields.Selection([('init', 'Chọn file'), ('preview', 'Xem trước')], default='init')
    preview_html = fields.Html(string='Dữ liệu xem trước')

    def action_export_template(self):
        """Sử dụng luôn file export hiện tại làm mẫu"""
        return {
            'type': 'ir.actions.act_url',
            'url': '/dl_salary_kpi/export_dependents',
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

        rel_map = {
            'Con': 'child',
            'Vợ/Chồng': 'spouse',
            'Bố/Mẹ': 'parent',
            'Anh/Chị/Em': 'sibling',
            'Khác': 'other'
        }

        parsed_data = []
        # Bắt đầu đọc từ dòng 2 (bỏ qua header)
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
            if not row or not any(row[1:4]): # Kiểm tra có dữ liệu cơ bản không
                continue
            
            # Cấu trúc mới: 
            # 0:STT, 1:Tên NV, 2:MST NV, 3:Tên NPT, 4:Quan hệ, 5:MST NPT, 6:CCCD NPT, 7:Trạng thái, 8:Ghi chú
            mst_nv = str(row[2]).strip() if row[2] else False
            name_npt = str(row[3]).strip() if row[3] else False
            
            error = ""
            if not mst_nv:
                error = "Thiếu MST nhân viên."
            elif not name_npt:
                error = "Thiếu tên NPT."
            else:
                employee = self.env['hr.employee'].search([('dl_tax_id', '=', mst_nv)], limit=1)
                if not employee:
                    error = f"Không tìm thấy NV có MST '{mst_nv}'"

            parsed_data.append({
                'row_idx': row_idx,
                'employee_name_excel': str(row[1]) if row[1] else '',
                'mst_nv': mst_nv,
                'name_npt': name_npt,
                'relationship_vi': str(row[4]) if row[4] else 'Con',
                'relationship': rel_map.get(str(row[4]).strip() if row[4] else '', 'child'),
                'tax_id': str(row[5]).strip() if row[5] else '',
                'id_card': str(row[6]).strip() if row[6] else '',
                'active': True if not row[7] or str(row[7]).upper() == 'X' else False,
                'note': row[8] if len(row) > 8 else '',
                'error': error
            })
        return parsed_data

    def action_preview(self):
        parsed_data = self._read_excel_data()
        if not parsed_data:
            raise UserError("File Excel không có dữ liệu hợp lệ.")

        valid_count = sum(1 for d in parsed_data if not d['error'])
        error_count = len(parsed_data) - valid_count

        # Hiển thị 5 dòng đầu và 5 dòng cuối
        preview_rows = parsed_data[:5]
        if len(parsed_data) > 10:
            preview_rows.extend([None]) # Marker for "...""
            preview_rows.extend(parsed_data[-5:])
        elif len(parsed_data) > 5:
            preview_rows.extend(parsed_data[5:])

        html = f"""
        <div class="alert alert-info">
            <strong>Tổng số dòng đọc được:</strong> {len(parsed_data)}<br/>
            <strong>Hợp lệ:</strong> <span class="text-success">{valid_count}</span> | 
            <strong>Lỗi:</strong> <span class="text-danger">{error_count}</span>
        </div>
        <table class="table table-sm table-bordered">
            <thead class="table-light">
                <tr>
                    <th>Dòng</th>
                    <th>Tên NV</th>
                    <th>MST NV</th>
                    <th>Tên NPT</th>
                    <th>Quan hệ</th>
                    <th>MST NPT</th>
                    <th>CCCD NPT</th>
                    <th>Trạng thái dữ liệu</th>
                </tr>
            </thead>
            <tbody>
        """

        for row in preview_rows:
            if row is None:
                html += """<tr><td colspan="8" class="text-center"><strong>... (Các dòng bị ẩn) ...</strong></td></tr>"""
                continue
            
            row_class = "table-danger" if row['error'] else ""
            status_text = f"<span class='text-danger'><i class='fa fa-warning'></i> Lỗi: {row['error']}</span>" if row['error'] else "<span class='text-success'><i class='fa fa-check'></i> Hợp lệ</span>"
            
            html += f"""
                <tr class="{row_class}">
                    <td>{row['row_idx']}</td>
                    <td>{row['employee_name_excel']}</td>
                    <td>{row['mst_nv']}</td>
                    <td>{row['name_npt']}</td>
                    <td>{row['relationship_vi']}</td>
                    <td>{row['tax_id']}</td>
                    <td>{row['id_card']}</td>
                    <td>{status_text}</td>
                </tr>
            """
        html += "</tbody></table>"

        self.preview_html = html
        self.state = 'preview'
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dl.dependent.import',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_back(self):
        self.state = 'init'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dl.dependent.import',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_confirm_import(self):
        parsed_data = self._read_excel_data()
        
        count_created = 0
        count_updated = 0
        errors = []

        for row in parsed_data:
            if row['error']:
                errors.append(f"Dòng {row['row_idx']}: {row['error']}")
                continue
                
            employee = self.env['hr.employee'].search([('dl_tax_id', '=', row['mst_nv'])], limit=1)
            if not employee:
                continue

            vals = {
                'employee_id': employee.id,
                'name': row['name_npt'],
                'relationship': row['relationship'],
                'dependent_number': row['tax_id'],
                'dependent_id_card': row['id_card'],
                'note': row['note'],
                'active': row['active']
            }
            
            # Tìm bản ghi đã tồn tại (dựa trên nhân viên + tên NPT)
            domain = [
                ('employee_id', '=', employee.id),
                ('name', '=', row['name_npt'])
            ]
            
            existing = self.env['dl.dependent'].search(domain, limit=1)
            
            if existing:
                existing.write(vals)
                count_updated += 1
            else:
                self.env['dl.dependent'].create(vals)
                count_created += 1

        message = f"Hoàn tất! Tạo mới: {count_created}, Cập nhật: {count_updated}."
        if errors:
            message += f"\nLỗi phát sinh:\n" + "\n".join(errors[:10])
            if len(errors) > 10:
                message += f"\n... và {len(errors)-10} lỗi khác."

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Kết quả nhập liệu',
                'message': message,
                'type': 'success' if not errors else 'warning',
                'sticky': True if errors else False,
            }
        }

