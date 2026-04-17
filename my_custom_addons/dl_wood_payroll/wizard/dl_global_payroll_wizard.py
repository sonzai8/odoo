# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import io
import base64
from datetime import date
import calendar

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

class GlobalPayrollWizard(models.TransientModel):
    _name = 'dl.global.payroll.wizard'
    _description = 'Wizard xuất báo cáo lương tổng hợp toàn công ty'

    month = fields.Selection([
        ('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'), ('4', 'Tháng 4'),
        ('5', 'Tháng 5'), ('6', 'Tháng 6'), ('7', 'Tháng 7'), ('8', 'Tháng 8'),
        ('9', 'Tháng 9'), ('10', 'Tháng 10'), ('11', 'Tháng 11'), ('12', 'Tháng 12')
    ], string='Tháng', default=lambda self: str(date.today().month), required=True)
    year = fields.Integer(string='Năm', default=lambda self: date.today().year, required=True)

    def action_export_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Formats
        f_title = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 16})
        f_header = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#f2dede', 'border': 1, 'text_wrap': True})
        f_cell = workbook.add_format({'border': 1, 'valign': 'vcenter'})
        f_cell_center = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
        f_cell_money = workbook.add_format({'num_format': '#,##0 "₫"', 'border': 1, 'align': 'right', 'valign': 'vcenter'})
        f_cell_money_bold = workbook.add_format({'bold': True, 'num_format': '#,##0 "₫"', 'border': 1, 'align': 'right', 'valign': 'vcenter', 'bg_color': '#f9f9f9'})

        sheet = workbook.add_worksheet(f"Luong_Tong_Hop_{self.month}_{self.year}")
        
        # Headers setup
        headers = [
            "STT", "Họ và tên", "CCCD", "Xưởng", "Bộ phận", "Số công", "Tổng tiền lương", 
            "Phạt", "Công đoàn", "BHXH", "BHXH Thu Bù", "Tạm ứng", "Tổng", 
            "Giảm trừ gia cảnh", "Thuế TNCN", "Thực Lĩnh", "Chuyển khoản", "Tiền mặt", "Ký nhận"
        ]
        
        # Column width - Widened as requested
        col_widths = [6, 30, 18, 20, 20, 10, 18, 15, 15, 15, 15, 15, 18, 15, 15, 18, 18, 18, 18]
        for i, width in enumerate(col_widths):
            sheet.set_column(i, i, width)

        sheet.merge_range(0, 0, 0, len(headers)-1, f"BẢNG LƯƠNG TỔNG HỢP - THÁNG {self.month}/{self.year}", f_title)
        
        for i, header in enumerate(headers):
            sheet.write(2, i, header, f_header)

        # Data retrieval
        first_day = date(self.year, int(self.month), 1)
        _, last_day_num = calendar.monthrange(self.year, int(self.month))
        last_day = date(self.year, int(self.month), last_day_num)
        
        # Get all pooling results for the month
        pooling_results = self.env['dl.daily.pooling.result'].search([
            ('date', '>=', first_day),
            ('date', '<=', last_day)
        ])
        
        # Get confirmed Stevedore logs and lines
        stevedore_logs = self.env['dl.stevedore.log'].search([
            ('date', '>=', first_day),
            ('date', '<=', last_day),
            ('state', '=', 'confirmed')
        ])
        stevedore_lines = self.env['dl.stevedore.log.line'].search([
            ('log_id', 'in', stevedore_logs.ids)
        ])
        
        # Get ALL active employees and sort by Group then Name
        employees = self.env['hr.employee'].search([]).sorted(
            lambda e: (e.x_source_group_id.name or 'ZZZ', e.name or '')
        )
        
        row = 3
        stt = 1
        for emp in employees:
            emp_pooling = pooling_results.filtered(lambda p: p.employee_id.id == emp.id)
            total_work_days = sum(emp_pooling.mapped('actual_work_days'))
            # Base salary before fines: sum of (unit_price * work_days)
            # In our pooling result, final_salary = pool_unit_price * actual_work_days - daily_fine
            # But the user asked for "Tổng tiền lương (không bao gồm thưởng phạt)"
            total_salary = sum(p.pool_unit_price * p.actual_work_days for p in emp_pooling)
            
            # Add Stevedore salary
            emp_stevedore = stevedore_lines.filtered(lambda s: s.employee_id.id == emp.id)
            total_salary += sum(emp_stevedore.mapped('amount'))
            
            # Monthly fines
            fines = self.env['dl.employee.fine'].search([
                ('employee_id', '=', emp.id),
                ('date', '>=', first_day),
                ('date', '<=', last_day)
            ])
            total_fines = sum(fines.mapped('amount'))
            
            trade_union = 40000
            
            # Write data
            sheet.write(row, 0, stt, f_cell_center)
            sheet.write(row, 1, emp.name, f_cell)
            sheet.write(row, 2, emp.identification_id or '', f_cell)
            sheet.write(row, 3, emp.department_id.x_workshop_id.name or '', f_cell)
            sheet.write(row, 4, emp.department_id.name or '', f_cell)
            sheet.write(row, 5, total_work_days, f_cell_center)
            
            # Excel calculation helper (Excel rows are 1-indexed)
            x_row = row + 1
            # Columns indices: G=6, H=7, I=8, K=10, L=11, M=12, O=14, P=15
            sheet.write(row, 6, total_salary, f_cell_money) # Tổng tiền lương
            sheet.write(row, 7, total_fines, f_cell_money)  # Phạt
            sheet.write(row, 8, trade_union, f_cell_money)  # Công đoàn
            sheet.write(row, 9, 0, f_cell_money)            # BHXH (Blank)
            sheet.write(row, 10, 0, f_cell_money)           # BHXH Thu Bù (Blank)
            sheet.write(row, 11, 0, f_cell_money)           # Tạm ứng (Blank)
            
            # Tổng = (Salary - Fines - Trade Union - BHXH Thu Bu - Advance)
            # Cell index: M = Sum - Fine - Union - SHUI Arrears - Advance
            # In Excel: M[row] = G[row] - H[row] - I[row] - K[row] - L[row]
            sheet.write_formula(row, 12, f"=G{x_row}-H{x_row}-I{x_row}-K{x_row}-L{x_row}", f_cell_money_bold) # Tổng
            
            sheet.write(row, 13, 0, f_cell_money)           # Giảm trừ gia cảnh
            sheet.write(row, 14, 0, f_cell_money)           # Thuế TNCN (Blank)
            
            # Thực Lĩnh = Tổng - Thuế TNCN = M - O
            sheet.write_formula(row, 15, f"=M{x_row}-O{x_row}", f_cell_money_bold) # Thực lĩnh
            
            sheet.write(row, 16, 0, f_cell_money)           # Chuyển khoản
            sheet.write(row, 17, 0, f_cell_money)           # Tiền mặt
            sheet.write(row, 18, "", f_cell)                # Ký nhận
            
            row += 1
            stt += 1

        # Total row
        sheet.write(row, 0, "", f_header)
        sheet.merge_range(row, 1, row, 4, "TỔNG CỘNG", f_header)
        for i in range(5, 18):
            col_letter = chr(ord('A') + i) if i < 26 else 'A' + chr(ord('A') + i - 26) # basic handling
            # Use xl_col_to_name for safety
            col_name = xlsxwriter.utility.xl_col_to_name(i)
            sheet.write_formula(row, i, f"=SUM({col_name}4:{col_name}{row})", f_header)
        sheet.write(row, 18, "", f_header)

        workbook.close()
        output.seek(0)
        
        file_base64 = base64.b64encode(output.read())
        filename = f"Báo_cáo_lương_tổng_hợp_{self.month}_{self.year}.xlsx"
        
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': file_base64,
            'store_fname': filename,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
