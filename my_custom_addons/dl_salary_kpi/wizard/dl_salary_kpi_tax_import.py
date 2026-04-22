# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import io
import openpyxl

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

    def action_export_template(self):
        """Xuất file mẫu chứa danh sách nhân viên hiện có"""
        return {
            'type': 'ir.actions.act_url',
            'url': '/dl_salary_kpi/export_tax_employees',
            'target': 'new',
        }

    def action_verify(self):
        """Đọc file và hiển thị bản xem trước để người dùng kiểm tra"""
        if not self.file_data:
            raise UserError("Vui lòng chọn file Excel trước khi kiểm tra.")
        
        file_content = base64.b64decode(self.file_data)
        wb = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
        ws = wb.active

        self.line_ids.unlink()
        new_lines = []
        
        # Header map (cố định theo file xuất ra)
        # 0: STT, 1: ID, 2: Họ tên, 3: Tên riêng, 4: Email, 5: SĐT, 6: CCCD, 7: Giới tính
        # 8: MST, 9: Chức vụ thuế, 10: Phòng ban thuế, 11: Lương thuế
        
        for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
            # Nếu dòng trống hoàn toàn thì bỏ qua
            if not any(row[1:12]):
                continue
                
            emp_id = int(row[1]) if row[1] else False
            name = str(row[2]) if row[2] else ''
            dl_tax_id = str(row[8]) if row[8] else ''
            
            employee = False
            import_type = 'insert'
            error_msg = ""

            if emp_id:
                employee = self.env['hr.employee'].browse(emp_id)
                if not employee.exists():
                    error_msg = f"ID nhân viên {emp_id} không tồn tại trên hệ thống."
                else:
                    import_type = 'update'
            elif name and dl_tax_id:
                # Tìm kiếm theo Tên và MST nếu không có ID
                employee = self.env['hr.employee'].search([
                    ('name', '=', name),
                    ('dl_tax_id', '=', dl_tax_id)
                ], limit=1)
                if employee:
                    import_type = 'update'
                    emp_id = employee.id
                else:
                    import_type = 'insert'
            elif name:
                # Có tên nhưng không có MST và ID -> Mặc định là tạo mới
                import_type = 'insert'
            else:
                error_msg = "Dòng thiếu thông tin Họ tên để xác định nhân viên."

            new_lines.append((0, 0, {
                'employee_id': emp_id,
                'name': name,
                'dl_first_name': str(row[3]) if row[3] else '',
                'email': str(row[4]) if row[4] else '',
                'work_phone': str(row[5]) if row[5] else '',
                'identification_id': str(row[6]) if row[6] else '',
                'sex': str(row[7]) if row[7] else '',
                'dl_tax_id': dl_tax_id,
                'dl_tax_position': str(row[9]) if row[9] else '',
                'dl_tax_department': str(row[10]) if row[10] else '',
                'dl_tax_base_salary': float(row[11]) if row[11] else 0.0,
                'import_type': import_type,
                'error_msg': error_msg,
            }))
            
        self.write({
            'line_ids': new_lines,
            'state': 'verify'
        })
        
        return {
            'name': 'Kiểm tra thông tin nhập',
            'type': 'ir.actions.act_window',
            'res_model': 'dl.salary.kpi.tax.import',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_confirm_import(self):
        """Xác nhận cập nhật dữ liệu chính thức"""
        self.ensure_one()
        if any(l.error_msg for l in self.line_ids):
            raise UserError("Vui lòng xử lý hết các lỗi trước khi xác nhận.")
            
        count_create = 0
        count_update = 0
        
        for line in self.line_ids:
            vals = {
                'name': line.name,
                'dl_first_name': line.dl_first_name,
                'email': line.email,
                'work_phone': line.work_phone,
                'identification_id': line.identification_id,
                'sex': 'male' if line.sex == 'Nam' else 'female' if line.sex == 'Nữ' else 'other',
                'dl_tax_id': line.dl_tax_id,
                'dl_tax_position': line.dl_tax_position,
                'dl_tax_department': line.dl_tax_department,
                'dl_tax_base_salary': line.dl_tax_base_salary,
            }
            
            if line.import_type == 'update' and line.employee_id:
                employee = self.env['hr.employee'].browse(line.employee_id)
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
                'message': _('Đã xử lý: %s cập nhật, %s thêm mới.') % (count_update, count_create),
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
    dl_first_name = fields.Char(string='Tên riêng')
    email = fields.Char(string='Email')
    work_phone = fields.Char(string='SĐT')
    identification_id = fields.Char(string='Số CCCD')
    sex = fields.Char(string='Giới tính')
    dl_tax_id = fields.Char(string='Mã số thuế')
    dl_tax_position = fields.Char(string='Chức vụ thuế')
    dl_tax_department = fields.Char(string='Phòng ban thuế')
    dl_tax_base_salary = fields.Float(string='Lương thuế')
    
    import_type = fields.Selection([
        ('insert', 'Thêm mới'),
        ('update', 'Cập nhật')
    ], string='Loại hành động')
    
    error_msg = fields.Char(string='Lỗi', readonly=True)
