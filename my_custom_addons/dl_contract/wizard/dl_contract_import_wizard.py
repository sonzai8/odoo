# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import io
import base64
import zipfile
from datetime import datetime, date
import openpyxl

class DlContractImportWizard(models.TransientModel):
    _name = 'dl.contract.import.wizard'
    _description = 'Wizard Nhập/Xuất Hợp đồng hàng loạt'

    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company)
    only_no_contract = fields.Boolean(string='Chỉ xuất nhân viên chưa có HĐ', default=True, help='Nếu chọn, hệ thống chỉ xuất danh sách các nhân viên hiện tại chưa có hợp đồng nào đang hiệu lực.')
    
    excel_file = fields.Binary(string='File Excel nhập liệu')
    excel_filename = fields.Char(string='Tên file Excel')
    
    auto_confirm = fields.Boolean(string='Tự động xác nhận hiệu lực', default=True, help='Nếu chọn, các hợp đồng tạo thành công sẽ tự động chuyển sang trạng thái "Đang hiệu lực".')
    
    state = fields.Selection([
        ('choose', 'Nhập liệu/Xuất bản mẫu'),
        ('done', 'Hoàn tất')
    ], default='choose')
    
    result_msg = fields.Text(string='Kết quả xử lý', readonly=True)

    def action_export_template(self):
        self.ensure_one()
        # 1. Tìm nhân viên
        domain = [('company_id', '=', self.company_id.id)]
        if self.only_no_contract:
            domain.append(('dl_contract_state', '=', 'no_contract'))
        employees = self.env['hr.employee'].search(domain, order='name')

        if not employees:
            raise UserError(_("Không tìm thấy nhân viên nào phù hợp với bộ lọc."))

        # 2. Lấy danh mục Phòng ban, Chức danh, Loại HĐ
        contract_types = self.env['dl.contract.type'].search([('company_id', '=', self.company_id.id)])
        departments = self.env['hr.department'].search([('company_id', '=', self.company_id.id)])
        job_titles = self.env['dl.job.title'].search([('company_id', '=', self.company_id.id)])

        # 3. Tạo file excel
        wb = openpyxl.Workbook()
        
        # Sheet danh mục ẩn để làm Data Validation
        ws_dm = wb.create_sheet(title="DanhMuc")
        ws_dm.cell(row=1, column=1, value="Loại hợp đồng")
        ws_dm.cell(row=1, column=2, value="Phòng ban")
        ws_dm.cell(row=1, column=3, value="Chức danh")
        
        for idx, val in enumerate(contract_types.mapped('name'), start=2):
            ws_dm.cell(row=idx, column=1, value=val)
        for idx, val in enumerate(departments.mapped('name'), start=2):
            ws_dm.cell(row=idx, column=2, value=val)
        for idx, val in enumerate(job_titles.mapped('name'), start=2):
            ws_dm.cell(row=idx, column=3, value=val)
        
        ws_dm.sheet_state = 'hidden' # Ẩn sheet danh mục đi cho sạch sẽ

        # Sheet chính để nhập liệu
        ws_main = wb.active
        ws_main.title = "DanhSachNhanVien"

        headers = [
            "ID Nhân viên", 
            "Họ và tên", 
            "Số CCCD", 
            "Loại hợp đồng", 
            "Lương cơ bản", 
            "Ngày bắt đầu (dd/mm/yyyy)", 
            "Ngày kết thúc (dd/mm/yyyy)", 
            "Phòng ban", 
            "Chức danh"
        ]

        # Định dạng Header
        header_font = openpyxl.styles.Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = openpyxl.styles.PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        
        for col_idx, h in enumerate(headers, start=1):
            cell = ws_main.cell(row=1, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = openpyxl.styles.Alignment(horizontal="center", vertical="center", wrap_text=True)

        ws_main.row_dimensions[1].height = 28

        # Ghi thông tin nhân viên
        id_font = openpyxl.styles.Font(name="Calibri", size=10, color="808080")
        for row_idx, emp in enumerate(employees, start=2):
            c_id = ws_main.cell(row=row_idx, column=1, value=emp.id)
            c_id.font = id_font # Làm nhạt ID để người dùng biết ko được sửa
            c_id.alignment = openpyxl.styles.Alignment(horizontal="center")
            
            c_name = ws_main.cell(row=row_idx, column=2, value=emp.name)
            c_name.alignment = openpyxl.styles.Alignment(vertical="center")
            
            c_cccd = ws_main.cell(row=row_idx, column=3, value=emp.identification_id or '')
            c_cccd.alignment = openpyxl.styles.Alignment(horizontal="center", vertical="center")

            # Nếu nhân viên chưa có lương (từ hợp đồng) mà có dl_tax_base_salary > 0 thì điền vào template
            wage = 0.0
            if emp.dl_current_contract_id and emp.dl_current_contract_id.wage:
                wage = emp.dl_current_contract_id.wage
            if not wage and hasattr(emp, 'dl_tax_base_salary') and emp.dl_tax_base_salary > 0:
                wage = emp.dl_tax_base_salary
            
            if wage > 0:
                ws_main.cell(row=row_idx, column=5, value=wage)


        # Cấu hình Data Validation cho các cột dropdown và định dạng Ngày tháng
        from openpyxl.worksheet.datavalidation import DataValidation
        
        max_ct = len(contract_types)
        max_dept = len(departments)
        max_job = len(job_titles)
        max_row = len(employees) + 1

        dv_type = DataValidation(type="list", formula1=f"DanhMuc!$A$2:$A${max_ct + 1}" if max_ct > 0 else '""', allow_blank=True)
        dv_dept = DataValidation(type="list", formula1=f"DanhMuc!$B$2:$B${max_dept + 1}" if max_dept > 0 else '""', allow_blank=True)
        dv_job = DataValidation(type="list", formula1=f"DanhMuc!$C$2:$C${max_job + 1}" if max_job > 0 else '""', allow_blank=True)

        dv_type.error = 'Vui lòng chọn loại hợp đồng hợp lệ trong danh mục.'
        dv_type.errorTitle = 'Lựa chọn sai danh mục'
        dv_dept.error = 'Vui lòng chọn phòng ban hợp lệ trong danh mục.'
        dv_dept.errorTitle = 'Lựa chọn sai danh mục'
        dv_job.error = 'Vui lòng chọn chức danh hợp lệ trong danh mục.'
        dv_job.errorTitle = 'Lựa chọn sai danh mục'

        ws_main.add_data_validation(dv_type)
        ws_main.add_data_validation(dv_dept)
        ws_main.add_data_validation(dv_job)

        if max_row >= 2:
            dv_type.add(f"D2:D{max_row}")
            dv_dept.add(f"H2:H{max_row}")
            dv_job.add(f"I2:I{max_row}")
            
            # Format định dạng Ngày bắt đầu (cột 6 - F) và Ngày kết thúc (cột 7 - G)
            for r_idx in range(2, max_row + 1):
                ws_main.cell(row=r_idx, column=6).number_format = 'dd/mm/yyyy'
                ws_main.cell(row=r_idx, column=7).number_format = 'dd/mm/yyyy'

        # Tự động căn chỉnh độ rộng cột
        for col in ws_main.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws_main.column_dimensions[col_letter].width = max(max_len + 4, 12)

        # Lưu workbook
        fp = io.BytesIO()
        wb.save(fp)
        fp.seek(0)
        file_bytes = fp.read()
        
        self.write({
            'excel_file': base64.b64encode(file_bytes),
            'excel_filename': f"Template_Nhap_HD_{fields.Date.today().strftime('%Y%m%d')}.xlsx",
            'state': 'done',
            'result_msg': f"Đã xuất thành công template nhập hợp đồng chứa {len(employees)} nhân viên chưa có hợp đồng của công ty {self.company_id.name}. Vui lòng tải về, điền thông tin và import ngược lại."
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_import_data(self):
        self.ensure_one()
        if not self.excel_file:
            raise UserError(_("Vui lòng tải lên file Excel dữ liệu đã nhập."))

        # 1. Đọc file Excel
        excel_bytes = base64.b64decode(self.excel_file)
        excel_stream = io.BytesIO(excel_bytes)
        try:
            wb = openpyxl.load_workbook(excel_stream, data_only=True)
            ws = wb.active
        except Exception as e:
            raise UserError(_("Không thể đọc file Excel. Đảm bảo file đúng định dạng .xlsx. Chi tiết lỗi: %s") % str(e))

        def parse_date_val(val):
            if not val:
                return False
            if isinstance(val, (date, datetime)):
                return val.date() if isinstance(val, datetime) else val
            if isinstance(val, str):
                for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
                    try:
                        return datetime.strptime(val.strip(), fmt).date()
                    except ValueError:
                        continue
            return False

        # Quét dòng
        row_count = 0
        success_count = 0
        logs = []

        # Load các danh mục để tránh query trong vòng lặp
        ctype_obj = self.env['dl.contract.type']
        dept_obj = self.env['hr.department']
        job_obj = self.env['dl.job.title']
        employee_obj = self.env['hr.employee']
        contract_obj = self.env['dl.contract']

        for r in range(2, ws.max_row + 1):
            emp_id_val = ws.cell(row=r, column=1).value
            if emp_id_val is None:
                continue
            
            row_count += 1
            try:
                emp_id = int(float(str(emp_id_val).strip()))
            except ValueError:
                logs.append(f"Dòng {r}: ID Nhân viên '{emp_id_val}' không hợp lệ.")
                continue

            employee = employee_obj.browse(emp_id).exists()
            if not employee:
                logs.append(f"Dòng {r}: Không tìm thấy nhân viên ID {emp_id} trong hệ thống.")
                continue

            # Các thông tin hợp đồng nhập liệu từ cột mới
            type_name = ws.cell(row=r, column=4).value
            wage_val = ws.cell(row=r, column=5).value
            start_date_val = ws.cell(row=r, column=6).value
            end_date_val = ws.cell(row=r, column=7).value
            dept_name = ws.cell(row=r, column=8).value
            job_name = ws.cell(row=r, column=9).value

            if not type_name or not start_date_val:
                logs.append(f"Dòng {r} (Nhân viên: {employee.name}): Thiếu loại hợp đồng hoặc ngày bắt đầu hiệu lực.")
                continue

            # 1. Tìm loại hợp đồng
            ctype = ctype_obj.search([('name', '=ilike', str(type_name).strip()), ('company_id', '=', self.company_id.id)], limit=1)
            if not ctype:
                logs.append(f"Dòng {r} (Nhân viên: {employee.name}): Không tìm thấy loại HĐ '{type_name}' trong công ty.")
                continue

            # 2. Parse ngày tháng
            start_date = parse_date_val(start_date_val)
            if not start_date:
                logs.append(f"Dòng {r} (Nhân viên: {employee.name}): Ngày bắt đầu '{start_date_val}' sai định dạng.")
                continue

            end_date = parse_date_val(end_date_val)
            
            # 3. Tìm phòng ban & chức danh (nếu có nhập)
            dept_id = False
            if dept_name:
                dept = dept_obj.search([('name', '=ilike', str(dept_name).strip()), ('company_id', '=', self.company_id.id)], limit=1)
                if dept:
                    dept_id = dept.id
                else:
                    logs.append(f"Dòng {r} (Nhân viên: {employee.name}): Không tìm thấy Phòng ban '{dept_name}' trong công ty.")
            
            job_id = False
            if job_name:
                job = job_obj.search([('name', '=ilike', str(job_name).strip()), ('company_id', '=', self.company_id.id)], limit=1)
                if job:
                    job_id = job.id
                else:
                    logs.append(f"Dòng {r} (Nhân viên: {employee.name}): Không tìm thấy Chức danh '{job_name}' trong công ty.")

            # 4. Lương
            try:
                wage = float(wage_val) if wage_val is not None else 0.0
            except ValueError:
                wage = 0.0
                logs.append(f"Dòng {r} (Nhân viên: {employee.name}): Lương cơ bản '{wage_val}' sai định dạng số.")

            # 5. Tạo hợp đồng mới
            try:
                contract = contract_obj.create({
                    'employee_id': employee.id,
                    'contract_type_id': ctype.id,
                    'wage': wage,
                    'allowance': 0.0,
                    'date_start': start_date,
                    'date_end': end_date,
                    'department_id': dept_id or employee.department_id.id,
                    'job_title_id': job_id or employee.x_job_title_id.id,
                    'company_id': self.company_id.id,
                })
                
                if self.auto_confirm:
                    contract.action_confirm()

                success_count += 1
            except Exception as e:
                logs.append(f"Dòng {r} (Nhân viên: {employee.name}): Lỗi khi tạo Hợp đồng: {str(e)}")

        # Tạo thông điệp báo cáo
        summary = f"=== KẾT QUẢ NHẬP DỮ LIỆU ===\n"
        summary += f"- Tổng số dòng nhân viên được quét: {row_count}\n"
        summary += f"- Tạo hợp đồng thành công: {success_count} nhân viên\n"
        summary += f"- Số lượng dòng lỗi/cảnh báo: {len(logs)}\n\n"
        if logs:
            summary += "Chi tiết lỗi & Cảnh báo:\n" + "\n".join(logs)
        else:
            summary += "Tất cả hợp đồng đã được nhập và cập nhật thành công!"

        self.write({
            'state': 'done',
            'result_msg': summary
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_back_to_choose(self):
        self.ensure_one()
        self.write({
            'state': 'choose',
            'excel_file': False,
            'excel_filename': False,
            'result_msg': False,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

