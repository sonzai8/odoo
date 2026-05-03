# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import io
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, Protection
from datetime import date
import calendar

class AttendanceExportController(http.Controller):

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
        ws.freeze_panes = 'F4'

        company_name = request.env.company.name or "Duc Lam"
        title = f"FILE CHẤM CÔNG THÁNG {month.date_month.strftime('%m')} NĂM {month.date_month.strftime('%Y')} CÔNG TY {company_name}".upper()
        
        title_font = Font(size=16, bold=True)
        header_font = Font(bold=True)
        border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        alignment = Alignment(horizontal='center', vertical='center')
        
        sunday_fill = openpyxl.styles.PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")
        sunday_data_fill = openpyxl.styles.PatternFill(start_color="E6F2FF", end_color="E6F2FF", fill_type="solid")
        fill_cp = openpyxl.styles.PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid")
        fill_kp_o = openpyxl.styles.PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
        fill_dc = openpyxl.styles.PatternFill(start_color="E5CCFF", end_color="E5CCFF", fill_type="solid")
        fill_departed = openpyxl.styles.PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")

        ws.row_dimensions[1].height = 30
        ws.column_dimensions['A'].width = 6
        ws.column_dimensions['B'].width = 8
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 14
        ws.column_dimensions['F'].width = 10
        ws.column_dimensions['G'].width = 12
        ws.column_dimensions['H'].width = 8
        ws.column_dimensions['I'].width = 10

        last_col = 9 + 31 + 5
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col)
        title_cell = ws.cell(row=1, column=1, value=title)
        title_cell.font = title_font
        title_cell.alignment = alignment

        headers_main = ["STT", "Mã NV", "Họ và tên", "Mã số thuế", "Ngày sinh", "Giới tính", "Phòng ban thuế", "Chức vụ", "Lương cơ bản"]
        weekday_map = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
        last_day = calendar.monthrange(month.date_month.year, month.date_month.month)[1]

        for col, text in enumerate(headers_main, 1):
            cell = ws.cell(row=2, column=col, value=text)
            cell.font = header_font
            cell.border = border
            cell.alignment = alignment
            ws.merge_cells(start_row=2, start_column=col, end_row=3, end_column=col)

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
            ws.cell(row=row_num, column=8, value=line.dl_tax_position).border = border
            ws.cell(row=row_num, column=9, value=line.dl_tax_base_salary).border = border
            
            departure_date = line.employee_id.dl_departure_date
            for day in range(1, 32):
                col_idx = 10 + day - 1
                field_name = f"day_{day:02d}"
                att_type = getattr(line, field_name)
                code = att_type.code if att_type else ""
                cell = ws.cell(row=row_num, column=col_idx, value=code)
                cell.border = border
                cell.alignment = alignment
                
                d = None
                if day <= last_day:
                    d = date(month.date_month.year, month.date_month.month, day)
                
                if d and d.weekday() == 6:
                    cell.protection = Protection(locked=True)
                else:
                    cell.protection = Protection(locked=False)
                
                if departure_date and d and d > departure_date:
                    cell.fill = fill_departed
                elif code == 'CP':
                    cell.fill = fill_cp
                elif code in ['KP', 'Ô']:
                    cell.fill = fill_kp_o
                elif code == 'ĐC':
                    cell.fill = fill_dc
                elif d and d.weekday() == 6:
                    cell.fill = sunday_data_fill
                
            row = row_num
            ws.cell(row=row, column=41, value=f'=COUNTIF(J{row}:AN{row},"N")+(COUNTIF(J{row}:AN{row},"N/1")+COUNTIF(J{row}:AN{row},"N/2"))*0.5').border = border
            ws.cell(row=row, column=42, value=f'=COUNTIF(J{row}:AN{row},"Đ")+(COUNTIF(J{row}:AN{row},"Đ/1")+COUNTIF(J{row}:AN{row},"Đ/2"))*0.5').border = border
            ws.cell(row=row, column=43, value=f'=AO{row}+AP{row}').border = border
            ws.cell(row=row, column=44, value=f'=COUNTIF(J{row}:AN{row},"PL")').border = border
            ws.cell(row=row, column=45, value=f'=COUNTIF(J{row}:AN{row},"P")').border = border
            row_num += 1

        summary_headers = [("AO", "Công Ngày"), ("AP", "Công Đêm"), ("AQ", "Tổng Cộng"), ("AR", "Ngày Lễ"), ("AS", "Ngày Phép")]
        for i, (col_letter, text) in enumerate(summary_headers):
            col_idx = 41 + i
            cell = ws.cell(row=2, column=col_idx, value=text)
            cell.font = header_font
            cell.border = border
            cell.alignment = alignment
            ws.merge_cells(start_row=2, start_column=col_idx, end_row=3, end_column=col_idx)
            ws.column_dimensions[col_letter].width = 12

        ws_codes = wb.create_sheet("Ma cham cong")
        ws_codes.cell(row=1, column=1, value="Mã công").font = header_font
        ws_codes.cell(row=1, column=2, value="Tên loại công").font = header_font
        ws_codes.cell(row=1, column=3, value="Trọng số").font = header_font
        
        att_types = request.env['dl.salary.kpi.attendance.type'].search([('ot_type', '=', 'none')], order='weight desc')
        for idx, att in enumerate(att_types, 2):
            ws_codes.cell(row=idx, column=1, value=att.code)
            ws_codes.cell(row=idx, column=2, value=att.name)
            ws_codes.cell(row=idx, column=3, value=att.weight)
        
        from openpyxl.worksheet.datavalidation import DataValidation
        last_data_row = row_num - 1
        dv = DataValidation(type="list", formula1=f"'Ma cham cong'!$A$2:$A${len(att_types) + 1}", allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"J4:AN{last_data_row}")

        ws.auto_filter.ref = f"A3:AS{last_data_row}"
        wb.save(output)
        output.seek(0)
        filename = f"Bang_Cham_Cong_{month.date_month.strftime('%m_%Y')}.xlsx"
        return request.make_response(output.getvalue(), headers=[('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'), ('Content-Disposition', f'attachment; filename={filename}')])

    @http.route('/dl_salary_kpi/export_ot_attendance/<int:month_id>', type='http', auth='user')
    def export_ot_attendance(self, month_id, **kwargs):
        month = request.env['dl.salary.kpi.month'].browse(month_id)
        if not month.exists():
            return http.NotFound()

        output = io.BytesIO()
        wb = openpyxl.Workbook()
        wb.calculation.fullCalcOnLoad = True
        ws = wb.active
        ws.title = "Bang Cham Cong Lam Them"
        ws.freeze_panes = 'F4'

        title_font = Font(size=16, bold=True)
        header_font = Font(bold=True)
        border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        alignment = Alignment(horizontal='center', vertical='center')
        sunday_fill = openpyxl.styles.PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")
        sunday_data_fill = openpyxl.styles.PatternFill(start_color="E6F2FF", end_color="E6F2FF", fill_type="solid")
        ot_header_fill = openpyxl.styles.PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid")
        fill_cp = openpyxl.styles.PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid")
        fill_kp_o = openpyxl.styles.PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
        fill_dc = openpyxl.styles.PatternFill(start_color="E5CCFF", end_color="E5CCFF", fill_type="solid")
        fill_departed = openpyxl.styles.PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")

        ws.row_dimensions[1].height = 30
        ws.column_dimensions['A'].width = 6
        ws.column_dimensions['B'].width = 8
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 14
        ws.column_dimensions['F'].width = 10
        ws.column_dimensions['G'].width = 12
        ws.column_dimensions['H'].width = 8
        ws.column_dimensions['I'].width = 10

        last_col = 9 + 31 + 5 + 31 + 3
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col)
        title = f"BẢNG CHẤM CÔNG LÀM THÊM THÁNG {month.date_month.strftime('%m/%Y')}".upper()
        title_cell = ws.cell(row=1, column=1, value=title)
        title_cell.font = title_font
        title_cell.alignment = alignment

        headers_main = ["STT", "Mã NV", "Họ và tên", "Mã số thuế", "Ngày sinh", "Giới tính", "Phòng ban thuế", "Chức vụ", "Lương cơ bản"]
        for col, text in enumerate(headers_main, 1):
            cell = ws.cell(row=2, column=col, value=text)
            cell.font = header_font
            cell.border = border
            cell.alignment = alignment
            ws.merge_cells(start_row=2, start_column=col, end_row=3, end_column=col)

        last_day = calendar.monthrange(month.date_month.year, month.date_month.month)[1]
        weekday_map = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]

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

        summary_headers = ["Công Ngày", "Công Đêm", "Tổng Cộng", "Ngày Lễ", "Ngày Phép"]
        for i, text in enumerate(summary_headers):
            col_idx = 41 + i
            cell = ws.cell(row=2, column=col_idx, value=text)
            cell.font = header_font
            cell.border = border
            cell.alignment = alignment
            ws.merge_cells(start_row=2, start_column=col_idx, end_row=3, end_column=col_idx)
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = 12

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

        ot_summary_headers = ["Tăng ca Ngày", "Tăng ca Đêm", "Tổng Tăng ca"]
        for i, text in enumerate(ot_summary_headers):
            col_idx = 77 + i
            cell = ws.cell(row=2, column=col_idx, value=text)
            cell.font = header_font
            cell.border = border
            cell.alignment = alignment
            ws.merge_cells(start_row=2, start_column=col_idx, end_row=3, end_column=col_idx)
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = 15

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
            ws.cell(row=row_num, column=8, value=line.dl_tax_position).border = border
            ws.cell(row=row_num, column=9, value=line.dl_tax_base_salary).border = border
            
            departure_date = line.employee_id.dl_departure_date
            for day in range(1, 32):
                col_idx = 9 + day
                norm_att = getattr(line, f"day_{day:02d}")
                norm_code = norm_att.code if norm_att else ""
                cell = ws.cell(row=row_num, column=col_idx, value=norm_code)
                cell.border = border
                cell.alignment = alignment
                
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
                elif d and d.weekday() == 6:
                    cell.fill = sunday_data_fill

            row = row_num
            ws.cell(row=row, column=41, value=f'=COUNTIF(J{row}:AN{row},"N")+(COUNTIF(J{row}:AN{row},"N/1")+COUNTIF(J{row}:AN{row},"N/2"))*0.5').border = border
            ws.cell(row=row, column=42, value=f'=COUNTIF(J{row}:AN{row},"Đ")+(COUNTIF(J{row}:AN{row},"Đ/1")+COUNTIF(J{row}:AN{row},"Đ/2"))*0.5').border = border
            ws.cell(row=row, column=43, value=f'=AO{row}+AP{row}').border = border
            ws.cell(row=row, column=44, value=f'=COUNTIF(J{row}:AN{row},"PL")').border = border
            ws.cell(row=row, column=45, value=f'=COUNTIF(J{row}:AN{row},"P")').border = border

            for day in range(1, 32):
                col_idx = 45 + day
                ot_att = getattr(line, f"ot_day_{day:02d}")
                ot_code = ot_att.code if ot_att else ""
                cell = ws.cell(row=row_num, column=col_idx, value=ot_code)
                cell.border = border
                cell.alignment = alignment
                
                d = None
                if day <= last_day:
                    d = date(month.date_month.year, month.date_month.month, day)
                
                if d and d.weekday() == 6:
                    cell.protection = Protection(locked=False)
                else:
                    cell.protection = Protection(locked=True)
                
                if departure_date and d and d > departure_date:
                    cell.fill = fill_departed
                else:
                    cell.fill = ot_header_fill if not ot_att else sunday_data_fill

            formula_ot_n = f'=COUNTIF(AT{row}:BX{row},"0.5N")*0.5 + COUNTIF(AT{row}:BX{row},"CNN")*8 + COUNTIF(AT{row}:BX{row},"CNN/2")*4 + COUNTIF(AT{row}:BX{row},"LN")*8'
            ws.cell(row=row, column=77, value=formula_ot_n).border = border
            formula_ot_d = f'=COUNTIF(AT{row}:BX{row},"0.5Đ")*0.5 + COUNTIF(AT{row}:BX{row},"CNĐ")*8 + COUNTIF(AT{row}:BX{row},"CNĐ/2")*4 + COUNTIF(AT{row}:BX{row},"LĐ")*8'
            ws.cell(row=row, column=78, value=formula_ot_d).border = border
            ws.cell(row=row, column=79, value=f'=BY{row}+BZ{row}').border = border
            row_num += 1
            
        last_data_row = row_num - 1
        ws.auto_filter.ref = f"A3:CA{last_data_row}"

        ws_codes_ot = wb.create_sheet("Ma tang ca")
        ws_codes_ot.cell(row=1, column=1, value="Mã tăng ca").font = header_font
        ws_codes_ot.cell(row=1, column=2, value="Tên loại").font = header_font
        att_types_ot = request.env['dl.salary.kpi.attendance.type'].search([('ot_type', '!=', 'none')], order='weight desc')
        for idx, att in enumerate(att_types_ot, 2):
            ws_codes_ot.cell(row=idx, column=1, value=att.code)
            ws_codes_ot.cell(row=idx, column=2, value=att.name)

        from openpyxl.worksheet.datavalidation import DataValidation
        dv_ot = DataValidation(type="list", formula1=f"'Ma tang ca'!$A$2:$A${len(att_types_ot) + 1}", allow_blank=True)
        ws.add_data_validation(dv_ot)
        dv_ot.add(f"J4:AN{last_data_row}")
        dv_ot.add(f"AT4:BX{last_data_row}")

        wb.save(output)
        output.seek(0)
        filename = f"Cong_Lam_Them_{month.date_month.strftime('%m_%Y')}.xlsx"
        return request.make_response(output.getvalue(), headers=[('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'), ('Content-Disposition', f'attachment; filename={filename}')])
