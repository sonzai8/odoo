# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import io
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, Protection

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
        ws.freeze_panes = 'F4'
        ws.protection.sheet = True
        ws.protection.password = 'duclam'
        ws.protection.autoFilter = False # Cho phép dùng AutoFilter khi sheet bị khóa

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
        ws.row_dimensions[1].height = 30
        ws.column_dimensions['A'].width = 6   # STT
        ws.column_dimensions['B'].width = 8   # Mã NV
        ws.column_dimensions['C'].width = 20  # Họ và tên
        ws.column_dimensions['D'].width = 15  # Mã số thuế
        ws.column_dimensions['E'].width = 14  # Ngày sinh
        ws.column_dimensions['F'].width = 10  # Giới tính
        ws.column_dimensions['G'].width = 12  # Phòng ban thuế
        ws.column_dimensions['H'].width = 8   # Chức vụ
        ws.column_dimensions['I'].width = 10  # Lương cơ bản

        # Merge Title
        last_col = 9 + 31 + 5 + 31 + 3 # 9 (Info) + 31 (Norm) + 5 (Sum) + 31 (OT) + 3 (OT Sum)
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col)
        title = f"BẢNG CHẤM CÔNG LÀM THÊM THÁNG {month.date_month.strftime('%m/%Y')}".upper()
        title_cell = ws.cell(row=1, column=1, value=title)
        title_cell.font = title_font
        title_cell.alignment = alignment

        # Headers Row 2 & 3
        headers_main = ["STT", "Mã NV", "Họ và tên", "Mã số thuế", "Ngày sinh", "Giới tính", "Phòng ban thuế", "Chức vụ", "Lương cơ bản"]
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
            col = 9 + day
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
            col_idx = 41 + i
            cell = ws.cell(row=2, column=col_idx, value=text)
            cell.font = header_font
            cell.border = border
            cell.alignment = alignment
            ws.merge_cells(start_row=2, start_column=col_idx, end_row=3, end_column=col_idx)
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = 12

        # OT Headers (Columns 46-76: AT-BX)
        # Bỏ merge title ở hàng 2 để tránh xung đột với số ngày
        for day in range(1, 32):
            col = 45 + day
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

        # OT Summary Headers (Columns 77-79: BY-CA)
        ot_summary_headers = ["Tăng ca Ngày", "Tăng ca Đêm", "Tổng Tăng ca"]
        for i, text in enumerate(ot_summary_headers):
            col_idx = 77 + i
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
            ws.cell(row=row_num, column=2, value=line.employee_id.id).border = border
            ws.cell(row=row_num, column=3, value=line.employee_name).border = border
            ws.cell(row=row_num, column=4, value=line.dl_tax_id).border = border
            ws.cell(row=row_num, column=5, value=line.birthday).border = border
            ws.cell(row=row_num, column=6, value='Nam' if line.sex == 'male' else 'Nữ' if line.sex == 'female' else 'Khác').border = border
            ws.cell(row=row_num, column=7, value=line.dl_tax_department_id.name).border = border
            ws.cell(row=row_num, column=7).protection = Protection(locked=False)
            
            ws.cell(row=row_num, column=8, value=line.dl_tax_position).border = border
            ws.cell(row=row_num, column=8).protection = Protection(locked=False)
            
            ws.cell(row=row_num, column=9, value=line.dl_tax_base_salary).border = border
            ws.cell(row=row_num, column=9).protection = Protection(locked=False)
            
            departure_date = line.employee_id.dl_departure_date

            # Normal Data (J-AN)
            for day in range(1, 32):
                col_idx = 9 + day
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
                    if d.weekday() == 6: # Chủ nhật
                        cell.fill = sunday_data_fill
                        cell.protection = Protection(locked=False)
                    else: # Ngày thường
                        cell.protection = Protection(locked=True)
                else:
                    cell.protection = Protection(locked=True)

            # Summary Formulas
            row = row_num
            # Công Ngày (Cột 41 - AO): Đếm N (1.0) và N/1, N/2 (0.5)
            # Bây giờ Day 1 là cột 10 (J), Day 31 là cột 40 (AN)
            ws.cell(row=row, column=41, value=f'=COUNTIF(J{row}:AN{row},"N")+(COUNTIF(J{row}:AN{row},"N/1")+COUNTIF(J{row}:AN{row},"N/2"))*0.5').border = border
            ws.cell(row=row, column=42, value=f'=COUNTIF(J{row}:AN{row},"Đ")+(COUNTIF(J{row}:AN{row},"Đ/1")+COUNTIF(J{row}:AN{row},"Đ/2"))*0.5').border = border
            ws.cell(row=row, column=43, value=f'=AO{row}+AP{row}').border = border
            ws.cell(row=row, column=44, value=f'=COUNTIF(J{row}:AN{row},"PL")').border = border
            ws.cell(row=row, column=45, value=f'=COUNTIF(J{row}:AN{row},"P")').border = border

            # OT Data (AO-BS) with Auto-mapping
            for day in range(1, 32):
                col_idx = 45 + day
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
                
                # Sunday Locking logic (OT)
                d = None
                if day <= last_day:
                    d = date(month.date_month.year, month.date_month.month, day)
                
                if d and d.weekday() == 6: # Chủ nhật
                    cell.protection = Protection(locked=False)
                else: # Ngày thường
                    cell.protection = Protection(locked=True)
                
                d = None
                if day <= last_day:
                    d = date(month.date_month.year, month.date_month.month, day)

                if departure_date and d and d > departure_date:
                    cell.fill = fill_departed
                else:
                    cell.fill = ot_header_fill if not ot_att else sunday_data_fill # Nhấn mạnh ô có dữ liệu thật hoặc gợi ý

            # OT Summary Formulas
            row = row_num
            # Tăng ca Ngày: =COUNTIF(AT{row}:BX{row}, "0.5N")*0.5
            ws.cell(row=row, column=77, value=f'=COUNTIF(AT{row}:BX{row},"0.5N")*0.5').border = border
            # Tăng ca Đêm: =COUNTIF(AT{row}:BX{row}, "0.5Đ")*0.5
            ws.cell(row=row, column=78, value=f'=COUNTIF(AT{row}:BX{row},"0.5Đ")*0.5').border = border
            # Tổng Tăng ca: =BY{row}+BZ{row}
            ws.cell(row=row, column=79, value=f'=BY{row}+BZ{row}').border = border

            row_num += 1
            
        # Bật AutoFilter cho toàn bộ bảng
        last_data_row = row_num - 1
        if last_data_row >= 3:
            ws.auto_filter.ref = f"A3:CA{last_data_row}"

        # Validation and Codes sheet... (skipped for brevity, but I should keep it)
        ws_codes = wb.create_sheet("Ma cham cong")
        ws_codes.cell(row=1, column=1, value="Mã công").font = header_font
        ws_codes.cell(row=1, column=2, value="Tên loại công").font = header_font
        ws_codes.cell(row=1, column=3, value="Trọng số").font = header_font
        
        # Validation cho bảng làm thêm (Chỉ lấy mã tăng ca)
        att_types_ot = request.env['dl.salary.kpi.attendance.type'].search([('ot_type', '!=', 'none')], order='weight desc')
        ws_codes_ot = wb.create_sheet("Ma tang ca")
        ws_codes_ot.cell(row=1, column=1, value="Mã tăng ca").font = header_font
        ws_codes_ot.cell(row=1, column=2, value="Tên loại").font = header_font
        for idx, att in enumerate(att_types_ot, 2):
            ws_codes_ot.cell(row=idx, column=1, value=att.code)
            ws_codes_ot.cell(row=idx, column=2, value=att.name)

        from openpyxl.worksheet.datavalidation import DataValidation
        last_data_row = row_num - 1
        
        # Validation cho cột thường (J-AN) và cột OT (AT-BX)
        # Người dùng muốn: Các ô chủ nhật chỉ được chấm mã tăng ca
        dv_ot = DataValidation(
            type="list", 
            formula1=f"'Ma tang ca'!$A$2:$A${len(att_types_ot) + 1}", 
            allow_blank=True,
            showErrorMessage=True,
            errorTitle="Mã công không hợp lệ",
            error="Vui lòng chọn mã tăng ca từ danh sách hoặc xem sheet 'Ma tang ca'"
        )
        ws.add_data_validation(dv_ot)
        
        # Áp dụng cho cả 2 vùng J-AN và AT-BX (nhưng chỉ những ô được mở khóa - chủ nhật)
        dv_ot.add(f"J4:AN{last_data_row}")
        dv_ot.add(f"AT4:BX{last_data_row}")

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
        ws.freeze_panes = 'F4' # Đóng băng 9 cột đầu và 3 hàng đầu
        ws.protection.sheet = True
        ws.protection.password = 'duclam'
        ws.protection.autoFilter = False # Cho phép dùng AutoFilter khi sheet bị khóa


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
        ws.row_dimensions[1].height = 30
        ws.column_dimensions['A'].width = 6   # STT
        ws.column_dimensions['B'].width = 8   # Mã NV (small)
        ws.column_dimensions['C'].width = 20  # Họ và tên
        ws.column_dimensions['D'].width = 15  # Mã số thuế
        ws.column_dimensions['E'].width = 14  # Ngày sinh
        ws.column_dimensions['F'].width = 10  # Giới tính
        ws.column_dimensions['G'].width = 12  # Phòng ban thuế
        ws.column_dimensions['H'].width = 8   # Chức vụ
        ws.column_dimensions['I'].width = 10  # Lương cơ bản

        # Merge Title hàng 1
        last_col = 9 + 31 + 5 # 9 (Emp Info) + 31 (Days) + 5 (Summaries)
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col)
        title_cell = ws.cell(row=1, column=1, value=title)
        title_cell.font = title_font
        title_cell.alignment = alignment

        # Header hàng 2 (Số ngày) và Hàng 3 (Thứ)
        headers_main = ["STT", "Mã NV", "Họ và tên", "Mã số thuế", "Ngày sinh", "Giới tính", "Phòng ban thuế", "Chức vụ", "Lương cơ bản"]
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
            col = 9 + day
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

            ws.cell(row=row_num, column=2, value=line.employee_id.id).border = border
            ws.cell(row=row_num, column=3, value=line.employee_name).border = border
            ws.cell(row=row_num, column=4, value=line.dl_tax_id).border = border
            ws.cell(row=row_num, column=5, value=line.birthday).border = border
            ws.cell(row=row_num, column=6, value='Nam' if line.sex == 'male' else 'Nữ' if line.sex == 'female' else 'Khác').border = border
            ws.cell(row=row_num, column=7, value=line.dl_tax_department_id.name).border = border
            ws.cell(row=row_num, column=7).protection = Protection(locked=False)
            
            ws.cell(row=row_num, column=8, value=line.dl_tax_position).border = border
            ws.cell(row=row_num, column=8).protection = Protection(locked=False)
            
            ws.cell(row=row_num, column=9, value=line.dl_tax_base_salary).border = border
            ws.cell(row=row_num, column=9).protection = Protection(locked=False)
            
            departure_date = line.employee_id.dl_departure_date

            for day in range(1, 32):
                col_idx = 10 + day - 1 # Day 1 is column 10
                field_name = f"day_{day:02d}"
                att_type = getattr(line, field_name)
                code = att_type.code if att_type else ""
                cell = ws.cell(row=row_num, column=col_idx, value=code)
                cell.border = border
                cell.alignment = alignment
                
                # Sunday Locking logic
                d = None
                if day <= last_day:
                    d = date(month.date_month.year, month.date_month.month, day)
                
                if d and d.weekday() == 6:
                    cell.protection = Protection(locked=True)
                else:
                    cell.protection = Protection(locked=False)
                
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
                
            # THÊM CÁC CỘT TỔNG HỢP Ở CUỐI BẰNG CÔNG THỨC EXCEL (AO -> AS)
            row = row_num
            # Công Ngày (Cột 41 - AO): Đếm N (1.0) và N/1, N/2 (0.5)
            # Bây giờ Day 1 là cột 10 (J), Day 31 là cột 40 (AN)
            formula_n = f'=COUNTIF(J{row}:AN{row},"N")+(COUNTIF(J{row}:AN{row},"N/1")+COUNTIF(J{row}:AN{row},"N/2"))*0.5'
            cell_n = ws.cell(row=row, column=41, value=formula_n)
            cell_n.border = border
            cell_n.alignment = alignment

            # Công Đêm (Cột 42 - AP): Đếm Đ (1.0) và Đ/1, Đ/2 (0.5)
            formula_d = f'=COUNTIF(J{row}:AN{row},"Đ")+(COUNTIF(J{row}:AN{row},"Đ/1")+COUNTIF(J{row}:AN{row},"Đ/2"))*0.5'
            cell_d = ws.cell(row=row, column=42, value=formula_d)
            cell_d.border = border
            cell_d.alignment = alignment

            # Tổng Cộng (Cột 43 - AQ): = AO + AP
            formula_total = f'=AO{row}+AP{row}'
            cell_total = ws.cell(row=row, column=43, value=formula_total)
            cell_total.border = border
            cell_total.alignment = alignment
            cell_total.font = Font(bold=True, color="FF0000")

            # Ngày Lễ (Cột 44 - AR): Đếm PL
            formula_pl = f'=COUNTIF(J{row}:AN{row},"PL")'
            cell_pl = ws.cell(row=row, column=44, value=formula_pl)
            cell_pl.border = border
            cell_pl.alignment = alignment

            # Ngày Phép (Cột 45 - AS): Đếm P
            formula_p = f'=COUNTIF(J{row}:AN{row},"P")'
            cell_p = ws.cell(row=row, column=45, value=formula_p)
            cell_p.border = border
            cell_p.alignment = alignment

            row_num += 1

        # Header cho các cột tổng hợp (Hàng 2 & 3)
        summary_headers = [
            ("AO", "Công Ngày"), ("AP", "Công Đêm"), ("AQ", "Tổng Cộng"), 
            ("AR", "Ngày Lễ"), ("AS", "Ngày Phép")
        ]
        for i, (col_letter, text) in enumerate(summary_headers):
            col_idx = 41 + i
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
        ws_codes.cell(row=1, column=3, value="Trọng số").font = header_font
        
        att_types = request.env['dl.salary.kpi.attendance.type'].search([('ot_type', '=', 'none')], order='weight desc')
        for idx, att in enumerate(att_types, 2):
            ws_codes.cell(row=idx, column=1, value=att.code)
            ws_codes.cell(row=idx, column=2, value=att.name)
            ws_codes.cell(row=idx, column=3, value=att.weight)
        
        # Thêm Validation (Dropdown) cho sheet chính
        from openpyxl.worksheet.datavalidation import DataValidation
        last_data_row = row_num - 1
        validation_range = f"J4:AN{last_data_row}"
        
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

        # Bật AutoFilter cho toàn bộ bảng
        last_data_row = row_num - 1
        if last_data_row >= 3:
            ws.auto_filter.ref = f"A3:AS{last_data_row}"

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
        employees = request.env['hr.employee'].search([('active', 'in', [True, False])], order='dl_tax_department_id, dl_first_name')
        
        output = io.BytesIO()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Danh Sach Nhan Vien Thue"

        # Styles
        header_font = Font(bold=True)
        alignment = Alignment(horizontal='center', vertical='center')
        header_fill = openpyxl.styles.PatternFill(start_color="D6EAF8", end_color="D6EAF8", fill_type="solid")
        border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

        # Header
        headers = [
            "STT", "ID NV", "Họ và tên", "Tên riêng", "Số CCCD", "Ngày sinh", "Email", "SĐT", 
            "Giới tính", "Mã số thuế", "Chức vụ thuế", 
            "Phòng ban thuế", "Lương cơ bản thuế", "Ngày nghỉ việc"
        ]
        ws.row_dimensions[1].height = 30
        for col, text in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=text)
            cell.font = header_font
            cell.alignment = alignment
            cell.fill = header_fill
            cell.border = border
            cell.alignment = alignment

        # Tùy chỉnh độ rộng từng cột cụ thể
        ws.column_dimensions['A'].width = 6   # STT
        ws.column_dimensions['B'].width = 10  # ID NV
        ws.column_dimensions['C'].width = 20  # Họ và tên (~150px)
        ws.column_dimensions['D'].width = 15  # Tên riêng
        ws.column_dimensions['E'].width = 14  # Số CCCD (~100px)
        ws.column_dimensions['F'].width = 15  # Ngày sinh
        ws.column_dimensions['G'].width = 5   # Email (~30px - Rất hẹp)
        ws.column_dimensions['H'].width = 15  # SĐT
        ws.column_dimensions['I'].width = 12  # Giới tính
        ws.column_dimensions['J'].width = 18  # Mã số thuế
        ws.column_dimensions['K'].width = 18  # Chức vụ thuế (~120px)
        ws.column_dimensions['L'].width = 30  # Phòng ban thuế
        ws.column_dimensions['M'].width = 20  # Lương cơ bản thuế
        ws.column_dimensions['N'].width = 15  # Ngày nghỉ việc

        # Data
        for idx, emp in enumerate(employees, 1):
            row = idx + 1
            ws.row_dimensions[row].height = 25
            
            data = [
                idx, emp.id, emp.name, emp.dl_first_name, emp.identification_id,
                emp.birthday, emp.email, emp.work_phone, 
                'Nam' if emp.sex == 'male' else 'Nữ' if emp.sex == 'female' else 'Khác',
                emp.dl_tax_id, emp.dl_tax_position, 
                emp.dl_tax_department_id.name if emp.dl_tax_department_id else '', 
                emp.dl_tax_base_salary, emp.dl_departure_date
            ]
            
            for col, value in enumerate(data, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = border
                cell.alignment = Alignment(vertical='center', horizontal='left' if col in [3, 5] else 'center')
                
                # Định dạng Text cho các cột chứa số có số 0 ở đầu (CCCD, MST, SĐT)
                if col in [7, 8, 10]: # G: SĐT, H: CCCD, J: MST
                    cell.number_format = '@'
                    if value:
                        cell.value = str(value)

        # Thiết lập dữ liệu thành định dạng Table (Bảng) để dễ lọc và nhập liệu
        from openpyxl.worksheet.table import Table, TableStyleInfo
        
        # Xác định vùng dữ liệu (từ A1 đến cột N, dòng cuối cùng)
        last_row = len(employees) + 1
        if last_row > 1:
            table_range = f"A1:N{last_row}"
            table = Table(displayName="DanhSachNhanVienThue", ref=table_range)
            
            # Cấu hình Style cho Table
            style = TableStyleInfo(
                name="TableStyleMedium2", 
                showFirstColumn=False,
                showLastColumn=False, 
                showRowStripes=True, # Dòng kẻ sọc xen kẽ
                showColumnStripes=False
            )
            table.tableStyleInfo = style
            ws.add_table(table)

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

