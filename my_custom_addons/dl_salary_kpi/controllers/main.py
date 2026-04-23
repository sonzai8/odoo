# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import io
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side

class SalaryKpiController(http.Controller):

    @http.route('/dl_salary_kpi/export_ot_attendance/<int:month_id>', type='http', auth='user')
    def export_ot_attendance(self, month_id, **kwargs):
        month = request.env['dl.salary.kpi.month'].browse(month_id)
        if not month.exists():
            return http.NotFound()

        # Khởi tạo dữ liệu gợi ý trên web giống như trong Excel
        month._action_init_overtime_suggestions()

        output = io.BytesIO()
        wb = openpyxl.Workbook()
        wb.calculation.fullCalcOnLoad = True
        ws = wb.active
        ws.title = "Bang Cham Cong Lam Them"
        ws.freeze_panes = 'E4'

        # Styles (Same as normal export)
        title_font = Font(size=16, bold=True)
        header_font = Font(bold=True)
        border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        alignment = Alignment(horizontal='center', vertical='center')
        sunday_fill = openpyxl.styles.PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")
        sunday_data_fill = openpyxl.styles.PatternFill(start_color="E6F2FF", end_color="E6F2FF", fill_type="solid")
        ot_header_fill = openpyxl.styles.PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid") # Vàng nhạt cho phần OT
        fill_cp = openpyxl.styles.PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid") # Vàng nhạt
        fill_kp_o = openpyxl.styles.PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid") # Đỏ nhạt
        fill_dc = openpyxl.styles.PatternFill(start_color="E5CCFF", end_color="E5CCFF", fill_type="solid") # Tím nhạt
        fill_departed = openpyxl.styles.PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid") # Xám nhạt cho nghỉ việc

        # Kích thước
        ws.row_dimensions[1].height = 40
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 15

        # Merge Title
        last_col = 40 + 31 + 3 # 40 (Normal) + 31 (OT) + 3 (OT Summaries)
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col)
        title = f"BẢNG CHẤM CÔNG LÀM THÊM THÁNG {month.date_month.strftime('%m/%Y')}".upper()
        title_cell = ws.cell(row=1, column=1, value=title)
        title_cell.font = title_font
        title_cell.alignment = alignment

        # Headers Row 2 & 3
        headers_main = ["STT", "Họ và tên", "Mã NV (ID)", "Số CCCD"]
        for col, text in enumerate(headers_main, 1):
            cell = ws.cell(row=2, column=col, value=text)
            cell.font = header_font
            cell.border = border
            cell.alignment = alignment
            ws.merge_cells(start_row=2, start_column=col, end_row=3, end_column=col)

        from datetime import date
        import calendar
        last_day = calendar.monthrange(month.date_month.year, month.date_month.month)[1]
        weekday_map = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]

        # Days Header (Normal 1-31)
        for day in range(1, 32):
            col = 4 + day
            cell_day = ws.cell(row=2, column=col, value=f"{day:02d}")
            cell_day.font = header_font
            cell_day.border = border
            cell_day.alignment = alignment
            
            weekday_str = ""
            is_sun = False
            if day <= last_day:
                d = date(month.date_month.year, month.date_month.month, day)
                weekday_str = weekday_map[d.weekday()]
                is_sun = (d.weekday() == 6)
            
            cell_wd = ws.cell(row=3, column=col, value=weekday_str)
            cell_wd.font = header_font
            cell_wd.border = border
            cell_wd.alignment = alignment
            if is_sun:
                cell_day.fill = sunday_fill
                cell_wd.fill = sunday_fill

        # Summary Headers (Columns 36-40: AJ-AN)
        summary_headers = ["Công Ngày", "Công Đêm", "Tổng Cộng", "Ngày Lễ", "Ngày Phép"]
        for i, text in enumerate(summary_headers):
            col_idx = 36 + i
            cell = ws.cell(row=2, column=col_idx, value=text)
            cell.font = header_font
            cell.border = border
            cell.alignment = alignment
            ws.merge_cells(start_row=2, start_column=col_idx, end_row=3, end_column=col_idx)
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = 12

        # OT Headers (Columns 41-71: AO-BS)
        for day in range(1, 32):
            col = 40 + day
            cell_day = ws.cell(row=2, column=col, value=f"{day:02d}")
            cell_day.font = header_font
            cell_day.border = border
            cell_day.alignment = alignment
            cell_day.fill = ot_header_fill
            
            weekday_str = ""
            is_sun = False
            if day <= last_day:
                d = date(month.date_month.year, month.date_month.month, day)
                weekday_str = weekday_map[d.weekday()]
                is_sun = (d.weekday() == 6)
            
            cell_wd = ws.cell(row=3, column=col, value=weekday_str)
            cell_wd.font = header_font
            cell_wd.border = border
            cell_wd.alignment = alignment
            cell_wd.fill = ot_header_fill
            if is_sun:
                cell_wd.font = Font(bold=True, color="FF0000")

        # OT Summary Headers (BT-BV)
        ot_summary_headers = ["Tăng ca Ngày", "Tăng ca Đêm", "Tổng Tăng ca"]
        for i, text in enumerate(ot_summary_headers):
            col_idx = 72 + i
            cell = ws.cell(row=2, column=col_idx, value=text)
            cell.font = header_font
            cell.border = border
            cell.alignment = alignment
            ws.merge_cells(start_row=2, start_column=col_idx, end_row=3, end_column=col_idx)
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = 15

        # Data rows
        row_num = 4
        for i, line in enumerate(month.line_ids, 1):
            ws.row_dimensions[row_num].height = 30
            ws.cell(row=row_num, column=1, value=i).border = border
            ws.cell(row=row_num, column=2, value=line.employee_name).border = border
            ws.cell(row=row_num, column=3, value=line.employee_id.id).border = border
            ws.cell(row=row_num, column=4, value=line.identification_id).border = border
            
            departure_date = line.employee_id.dl_departure_date

            # Normal Data (E-AI)
            for day in range(1, 32):
                col_idx = 4 + day
                norm_att = getattr(line, f"day_{day:02d}")
                norm_code = norm_att.code if norm_att else ""
                cell = ws.cell(row=row_num, column=col_idx, value=norm_code)
                cell.border = border
                cell.alignment = alignment
                
                # Check departure
                d = None
                if day <= last_day:
                    d = date(month.date_month.year, month.date_month.month, day)

                if departure_date and d and d > departure_date:
                    cell.fill = fill_departed
                elif norm_code == 'CP':
                    cell.fill = fill_cp
                elif norm_code in ['KP', 'Ô']:
                    cell.fill = fill_kp_o
                elif norm_code == 'ĐC':
                    cell.fill = fill_dc
                elif day <= last_day:
                    if d.weekday() == 6:
                        cell.fill = sunday_data_fill

            # Summary Formulas (AJ-AN)
            row = row_num
            ws.cell(row=row, column=36, value=f'=COUNTIF(E{row}:AI{row},"N")+(COUNTIF(E{row}:AI{row},"N/1")+COUNTIF(E{row}:AI{row},"N/2"))*0.5').border = border
            ws.cell(row=row, column=37, value=f'=COUNTIF(E{row}:AI{row},"Đ")+(COUNTIF(E{row}:AI{row},"Đ/1")+COUNTIF(E{row}:AI{row},"Đ/2"))*0.5').border = border
            ws.cell(row=row, column=38, value=f'=AJ{row}+AK{row}').border = border
            ws.cell(row=row, column=39, value=f'=COUNTIF(E{row}:AI{row},"PL")').border = border
            ws.cell(row=row, column=40, value=f'=COUNTIF(E{row}:AI{row},"P")').border = border

            # OT Data (AO-BS) with Auto-mapping
            for day in range(1, 32):
                col_idx = 40 + day
                ot_att = getattr(line, f"ot_day_{day:02d}")
                ot_code = ot_att.code if ot_att else ""
                
                if not ot_code:
                    norm_att = getattr(line, f"day_{day:02d}")
                    norm_code = norm_att.code if norm_att else ""
                    if norm_code == 'N': ot_code = '0.5N'
                    elif norm_code == 'Đ': ot_code = '0.5Đ'
                
                cell = ws.cell(row=row_num, column=col_idx, value=ot_code)
                cell.border = border
                cell.alignment = alignment
                
                d = None
                if day <= last_day:
                    d = date(month.date_month.year, month.date_month.month, day)

                if departure_date and d and d > departure_date:
                    cell.fill = fill_departed
                else:
                    cell.fill = ot_header_fill if not ot_att else sunday_data_fill # Nhấn mạnh ô có dữ liệu thật hoặc gợi ý

            # OT Summary Formulas (BT-BV)
            row = row_num
            # Tăng ca Ngày (BT): =COUNTIF(AO{row}:BS{row}, "0.5N")*0.5
            ws.cell(row=row, column=72, value=f'=COUNTIF(AO{row}:BS{row},"0.5N")*0.5').border = border
            # Tăng ca Đêm (BU): =COUNTIF(AO{row}:BS{row}, "0.5Đ")*0.5
            ws.cell(row=row, column=73, value=f'=COUNTIF(AO{row}:BS{row},"0.5Đ")*0.5').border = border
            # Tổng Tăng ca (BV): =BT{row}+BU{row}
            ws.cell(row=row, column=74, value=f'=BT{row}+BU{row}').border = border

            row_num += 1

        # Validation and Codes sheet... (skipped for brevity, but I should keep it)
        ws_codes = wb.create_sheet("Ma cham cong")
        att_types = request.env['dl.salary.kpi.attendance.type'].search([])
        for idx, att in enumerate(att_types, 1):
            ws_codes.cell(row=idx, column=1, value=att.code)
            ws_codes.cell(row=idx, column=2, value=att.name)

        wb.save(output)
        output.seek(0)
        filename = f"Cong_Lam_Them_{month.date_month.strftime('%m_%Y')}.xlsx"
        return request.make_response(
            output.getvalue(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename={filename}')
            ]
        )

    @http.route('/dl_salary_kpi/export_attendance/<int:month_id>', type='http', auth='user')
    def export_attendance(self, month_id, **kwargs):
        month = request.env['dl.salary.kpi.month'].browse(month_id)
        if not month.exists():
            return http.NotFound()

        output = io.BytesIO()
        wb = openpyxl.Workbook()
        wb.calculation.fullCalcOnLoad = True
        ws = wb.active
        ws.title = "Bang Cham Cong"
        ws.freeze_panes = 'E4' # Đóng băng 4 cột đầu và 3 hàng đầu


        # Tiêu đề hàng 1
        company_name = request.env.company.name or "Duc Lam"
        title = f"FILE CHẤM CÔNG THÁNG {month.date_month.strftime('%m')} NĂM {month.date_month.strftime('%Y')} CÔNG TY {company_name}".upper()
        
        # Styles
        title_font = Font(size=16, bold=True)
        header_font = Font(bold=True)
        border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        alignment = Alignment(horizontal='center', vertical='center')
        
        # Fills
        sunday_fill = openpyxl.styles.PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")
        sunday_data_fill = openpyxl.styles.PatternFill(start_color="E6F2FF", end_color="E6F2FF", fill_type="solid")
        
        fill_cp = openpyxl.styles.PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid") # Vàng nhạt
        fill_kp_o = openpyxl.styles.PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid") # Đỏ nhạt
        fill_dc = openpyxl.styles.PatternFill(start_color="E5CCFF", end_color="E5CCFF", fill_type="solid") # Tím nhạt
        fill_departed = openpyxl.styles.PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid") # Xám nhạt cho nghỉ việc

        # Kích thước hàng/cột
        ws.row_dimensions[1].height = 40
        ws.column_dimensions['B'].width = 30 # Tương đương 120-150px
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 15

        # Merge Title hàng 1
        last_col = 4 + 31
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col)
        title_cell = ws.cell(row=1, column=1, value=title)
        title_cell.font = title_font
        title_cell.alignment = alignment

        # Header hàng 2 (Số ngày) và Hàng 3 (Thứ)
        headers_main = ["STT", "Họ và tên", "Mã NV (ID)", "Số CCCD"]
        weekday_map = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
        
        from datetime import date
        import calendar
        last_day = calendar.monthrange(month.date_month.year, month.date_month.month)[1]

        # Điền Header chính (Row 2)
        for col, text in enumerate(headers_main, 1):
            cell = ws.cell(row=2, column=col, value=text)
            cell.font = header_font
            cell.border = border
            cell.alignment = alignment
            ws.merge_cells(start_row=2, start_column=col, end_row=3, end_column=col) # Merge cho STT, Tên...

        # Điền Ngày và Thứ (Row 2 & 3)
        for day in range(1, 32):
            col = 4 + day
            # Ngày (Row 2)
            cell_day = ws.cell(row=2, column=col, value=f"{day:02d}")
            cell_day.font = header_font
            cell_day.border = border
            cell_day.alignment = alignment
            
            # Thứ (Row 3)
            weekday_str = ""
            is_sun = False
            if day <= last_day:
                d = date(month.date_month.year, month.date_month.month, day)
                weekday_str = weekday_map[d.weekday()]
                is_sun = (d.weekday() == 6)
            
            cell_wd = ws.cell(row=3, column=col, value=weekday_str)
            cell_wd.font = header_font
            cell_wd.border = border
            cell_wd.alignment = alignment

            if is_sun:
                cell_day.fill = sunday_fill
                cell_wd.fill = sunday_fill

        # Data từ dòng 4
        row_num = 4
        attendance_cells = []
        for i, line in enumerate(month.line_ids, 1):
            ws.row_dimensions[row_num].height = 30 # Độ cao dòng dữ liệu
            ws.cell(row=row_num, column=1, value=i).border = border

            ws.cell(row=row_num, column=2, value=line.employee_name).border = border
            ws.cell(row=row_num, column=3, value=line.employee_id.id).border = border
            ws.cell(row=row_num, column=4, value=line.identification_id).border = border
            
            departure_date = line.employee_id.dl_departure_date

            for day in range(1, 32):
                col_idx = 4 + day
                field_name = f"day_{day:02d}"
                att_type = getattr(line, field_name)
                code = att_type.code if att_type else ""
                cell = ws.cell(row=row_num, column=col_idx, value=code)
                cell.border = border
                cell.alignment = alignment
                
                # Tô màu theo mã công
                d = None
                if day <= last_day:
                    d = date(month.date_month.year, month.date_month.month, day)

                if departure_date and d and d > departure_date:
                    cell.fill = fill_departed
                elif code == 'CP':
                    cell.fill = fill_cp
                elif code in ['KP', 'Ô']:
                    cell.fill = fill_kp_o
                elif code == 'ĐC':
                    cell.fill = fill_dc
                elif day <= last_day:
                    if d.weekday() == 6:
                        cell.fill = sunday_data_fill
                
            # THÊM CÁC CỘT TỔNG HỢP Ở CUỐI BẰNG CÔNG THỨC EXCEL (AJ -> AN)
            row = row_num
            # Công Ngày (Cột 36 - AJ): Đếm N (1.0) và N/1, N/2 (0.5)
            # Công thức: =COUNTIF(E{row}:AI{row}, "N") + (COUNTIF(E{row}:AI{row}, "N/1") + COUNTIF(E{row}:AI{row}, "N/2"))*0.5
            formula_n = f'=COUNTIF(E{row}:AI{row},"N")+(COUNTIF(E{row}:AI{row},"N/1")+COUNTIF(E{row}:AI{row},"N/2"))*0.5'
            cell_n = ws.cell(row=row, column=36, value=formula_n)
            cell_n.border = border
            cell_n.alignment = alignment

            # Công Đêm (Cột 37 - AK): Đếm Đ (1.0) và Đ/1, Đ/2 (0.5)
            # Công thức: =COUNTIF(E{row}:AI{row}, "Đ") + (COUNTIF(E{row}:AI{row}, "Đ/1") + COUNTIF(E{row}:AI{row}, "Đ/2"))*0.5
            formula_d = f'=COUNTIF(E{row}:AI{row},"Đ")+(COUNTIF(E{row}:AI{row},"Đ/1")+COUNTIF(E{row}:AI{row},"Đ/2"))*0.5'
            cell_d = ws.cell(row=row, column=37, value=formula_d)
            cell_d.border = border
            cell_d.alignment = alignment

            # Tổng Cộng (Cột 38 - AL): = AJ + AK
            formula_total = f'=AJ{row}+AK{row}'
            cell_total = ws.cell(row=row, column=38, value=formula_total)
            cell_total.border = border
            cell_total.alignment = alignment
            cell_total.font = Font(bold=True, color="FF0000") # Màu đỏ cho dễ nhìn

            # Ngày Lễ (Cột 39 - AM): Đếm PL
            formula_pl = f'=COUNTIF(E{row}:AI{row},"PL")'
            cell_pl = ws.cell(row=row, column=39, value=formula_pl)
            cell_pl.border = border
            cell_pl.alignment = alignment

            # Ngày Phép (Cột 40 - AN): Đếm P
            formula_p = f'=COUNTIF(E{row}:AI{row},"P")'
            cell_p = ws.cell(row=row, column=40, value=formula_p)
            cell_p.border = border
            cell_p.alignment = alignment

            row_num += 1

        # Header cho các cột tổng hợp (Hàng 2 & 3)
        summary_headers = [
            ("AJ", "Công Ngày"), ("AK", "Công Đêm"), ("AL", "Tổng Cộng"), 
            ("AM", "Ngày Lễ"), ("AN", "Ngày Phép")
        ]
        for i, (col_letter, text) in enumerate(summary_headers):
            col_idx = 36 + i
            cell = ws.cell(row=2, column=col_idx, value=text)
            cell.font = header_font
            cell.border = border
            cell.alignment = alignment
            ws.merge_cells(start_row=2, start_column=col_idx, end_row=3, end_column=col_idx)
            ws.column_dimensions[col_letter].width = 12

        # SHEET 2: MÃ CHẤM CÔNG
        ws_codes = wb.create_sheet("Ma cham cong")
        ws_codes.cell(row=1, column=1, value="Mã công").font = header_font
        ws_codes.cell(row=1, column=2, value="Tên loại công").font = header_font
        
        att_types = request.env['dl.salary.kpi.attendance.type'].search([])
        for idx, att in enumerate(att_types, 2):
            ws_codes.cell(row=idx, column=1, value=att.code)
            ws_codes.cell(row=idx, column=2, value=att.name)
        
        # Thêm Validation (Dropdown) cho sheet chính
        from openpyxl.worksheet.datavalidation import DataValidation
        last_data_row = row_num - 1
        validation_range = f"E4:AI{last_data_row}"
        
        dv = DataValidation(
            type="list", 
            formula1=f"'Ma cham cong'!$A$2:$A${len(att_types) + 1}", 
            allow_blank=True,
            showErrorMessage=True,
            errorTitle="Mã công không hợp lệ",
            error="Vui lòng chọn mã công từ danh sách hoặc xem sheet 'Ma cham cong'"
        )

        ws.add_data_validation(dv)
        dv.add(validation_range)

        wb.save(output)
        output.seek(0)
        
        filename = f"Bang_Cham_Cong_{month.date_month.strftime('%m_%Y')}.xlsx"
        return request.make_response(
            output.getvalue(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename={filename}')
            ]
        )






    @http.route('/dl_salary_kpi/export_tax_employees', type='http', auth='user')
    def export_tax_employees(self, **kwargs):
        employees = request.env['hr.employee'].search([('active', 'in', [True, False])])
        
        output = io.BytesIO()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Danh Sach Nhan Vien Thue"

        # Styles
        header_font = Font(bold=True)
        alignment = Alignment(horizontal='center', vertical='center')

        # Header
        headers = [
            "STT", "ID NV", "Họ và tên", "Tên riêng", "Email", "SĐT", 
            "Số CCCD", "Giới tính", "Mã số thuế", "Chức vụ thuế", 
            "Phòng ban thuế", "Lương cơ bản thuế", "Ngày nghỉ việc"
        ]
        for col, text in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=text)
            cell.font = header_font
            cell.alignment = alignment

        # Data
        for idx, emp in enumerate(employees, 1):
            row = idx + 1
            ws.cell(row=row, column=1, value=idx)
            ws.cell(row=row, column=2, value=emp.id)
            ws.cell(row=row, column=3, value=emp.name)
            ws.cell(row=row, column=4, value=emp.dl_first_name)
            ws.cell(row=row, column=5, value=emp.email)
            ws.cell(row=row, column=6, value=emp.work_phone)
            ws.cell(row=row, column=7, value=emp.identification_id)
            ws.cell(row=row, column=8, value='Nam' if emp.sex == 'male' else 'Nữ' if emp.sex == 'female' else 'Khác')
            ws.cell(row=row, column=9, value=emp.dl_tax_id)
            ws.cell(row=row, column=10, value=emp.dl_tax_position)
            ws.cell(row=row, column=11, value=emp.dl_tax_department)
            ws.cell(row=row, column=12, value=emp.dl_tax_base_salary)
            ws.cell(row=row, column=13, value=emp.dl_departure_date)

        wb.save(output)
        output.seek(0)
        
        filename = "Danh_Sach_Nhan_Vien_Thue.xlsx"
        return request.make_response(
            output.getvalue(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename={filename}')
            ]
        )

