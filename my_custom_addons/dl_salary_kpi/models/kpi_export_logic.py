# -*- coding: utf-8 -*-
import base64
import io
import logging
from calendar import monthrange
from odoo import _
from odoo.exceptions import UserError
from odoo.tools import file_path
import copy

_logger = logging.getLogger(__name__)

try:
    from openpyxl import load_workbook
    from openpyxl.cell.cell import MergedCell
    from openpyxl.styles import Alignment
except ImportError:
    load_workbook = None

def _fill_placeholder(ws, row, col, placeholders):
    """
    Tìm và thay thế các mã {placeholder} trong ô.
    Giữ nguyên các thành phần khác trong văn bản của ô.
    """
    cell = ws.cell(row=row, column=col)
    if not cell.value:
        return

    val = str(cell.value)
    has_placeholder = False
    for key, value in placeholders.items():
        placeholder = f"{{{key}}}"
        if placeholder in val:
            val = val.replace(placeholder, str(value if value is not None else ''))
            has_placeholder = True
    
    if not has_placeholder:
        return

    # Thử chuyển về số nếu ô chỉ chứa kết quả là số để Excel tính toán được
    try:
        if val.isdigit():
            cell.value = int(val)
        else:
            try:
                # Kiểm tra nếu là số thực
                if '.' in val and val.replace('.', '', 1).isdigit():
                    cell.value = float(val)
                else:
                    cell.value = val
            except ValueError:
                cell.value = val
    except:
        cell.value = val

def _copy_row_formatting(ws, source_row, target_row, copy_value=False):
    """
    Sao chép định dạng từ dòng nguồn sang dòng đích.
    Nếu copy_value=True, sao chép cả nội dung (chứa placeholder).
    """
    for col in range(1, ws.max_column + 1):
        source_cell = ws.cell(row=source_row, column=col)
        target_cell = ws.cell(row=target_row, column=col)
        
        if copy_value:
            target_cell.value = source_cell.value
            
        if source_cell.has_style:
            target_cell.font = copy.copy(source_cell.font)
            target_cell.border = copy.copy(source_cell.border)
            target_cell.fill = copy.copy(source_cell.fill)
            target_cell.number_format = source_cell.number_format
            target_cell.protection = copy.copy(source_cell.protection)
            target_cell.alignment = copy.copy(source_cell.alignment)
            
    if ws.row_dimensions[source_row].height:
        ws.row_dimensions[target_row].height = ws.row_dimensions[source_row].height

def export_kpi_point_excel(record):
    """
    Logic chính xử lý xuất file Excel điểm KPI.
    """
    if not load_workbook:
        raise UserError(_("Thư viện openpyxl chưa được cài đặt."))

    try:
        template_path = file_path('dl_salary_kpi/static/src/templates/TEMPLATE_KPI_2026.xlsx')
    except FileNotFoundError:
        raise UserError(_("Không tìm thấy file mẫu Excel tại static/src/templates/TEMPLATE_KPI_2026.xlsx"))

    wb = load_workbook(template_path)
    if 'TEMPLATE_KPI_POINT' not in wb.sheetnames:
        raise UserError(_("Không tìm thấy sheet TEMPLATE_KPI_POINT trong file mẫu."))
    if 'TEMPLATE_KPI_AMOUNT' not in wb.sheetnames:
        raise UserError(_("Không tìm thấy sheet TEMPLATE_KPI_AMOUNT trong file mẫu."))
    
    template_sheet_point = wb['TEMPLATE_KPI_POINT']
    template_sheet_amount = wb['TEMPLATE_KPI_AMOUNT']
    
    # Nhóm nhân viên theo phòng ban
    dept_groups = {}
    for line in record.line_ids:
        dept = line.dl_tax_department_id
        dept_id = dept.id if dept else 0
        if dept_id not in dept_groups:
            dept_groups[dept_id] = {
                'name': dept.name if dept else 'Khác',
                'lines': []
            }
        dept_groups[dept_id]['lines'].append(line)

    month_date = record.date_month
    month_str = month_date.strftime('%m')
    year_str = month_date.strftime('%Y')
    last_day = monthrange(month_date.year, month_date.month)[1]
    company = record.env.company

    # Tạo các sheet ĐIỂM KPI cho từng phòng ban trước
    for dept_id in sorted(dept_groups.keys()):
        dept_info = dept_groups[dept_id]
        dept_name = dept_info['name']
        lines = sorted(dept_info['lines'], key=lambda l: (l.employee_name or ''))
        
        # --- XỬ LÝ SHEET ĐIỂM KPI ---
        ws = wb.copy_worksheet(template_sheet_point)
        safe_dept_name = dept_name[:20]
        ws.title = f"{safe_dept_name} - Điểm KPI"
        
        # 1. Header
        _fill_placeholder(ws, 1, 1, {'company_name': company.name})
        _fill_placeholder(ws, 2, 1, {'tax_number': company.vat or ''})
        _fill_placeholder(ws, 3, 1, {'month': month_str, 'year': year_str})
        
        # Merge và căn giữa ô A3 sau khi điền
        ws.merge_cells('A3:H3')
        ws['A3'].alignment = Alignment(horizontal='center', vertical='center')
        
        # Ô A5: Bộ phận
        _fill_placeholder(ws, 5, 1, {'department': dept_name})
        ws.merge_cells('A5:B5')
        
        # 2. Điền dữ liệu nhân viên (Bắt đầu từ hàng 6)
        # Chúng ta sẽ không dùng insert_rows vì nó rất chậm. 
        # Thay vào đó, chúng ta sẽ ghi trực tiếp vào các hàng và copy formatting nếu cần.
        data_row_start = 6
        
        for i, line in enumerate(lines):
            row_idx = data_row_start + i
            
            # Chỉ sao chép định dạng cho các dòng sau dòng đầu tiên
            if i > 0:
                _copy_row_formatting(ws, data_row_start, row_idx, copy_value=False)
            
            # Ghi dữ liệu vào các cột
            ws.cell(row=row_idx, column=1, value=i + 1)
            ws.cell(row=row_idx, column=2, value=line.employee_name or '')
            ws.cell(row=row_idx, column=3, value=line.kpi_c1_productivity or 0)
            ws.cell(row=row_idx, column=4, value=line.kpi_c2_discipline or 0)
            ws.cell(row=row_idx, column=5, value=line.kpi_c3_teamwork or 0)
            ws.cell(row=row_idx, column=6, value=line.kpi_c4_5s or 0)
            ws.cell(row=row_idx, column=7, value=line.kpi_c5_saving or 0)
            ws.cell(row=row_idx, column=8, value=line.payroll_kpi_score or 0)

        # 3. Footer (Ngày tháng năm)
        # Bắt đầu từ 7. Sau khi chèn len(lines)-1 hàng, nó nằm ở 7 + len(lines) - 1 = 6 + len(lines)
        footer_date_row = 6 + len(lines)
        _fill_placeholder(ws, footer_date_row, 5, {'last_day_of_month': last_day, 'month': month_str, 'year': year_str})

    # Tạo các sheet TIỀN KPI cho từng phòng ban (sau khi đã tạo xong Điểm KPI)
    for dept_id in sorted(dept_groups.keys()):
        dept_info = dept_groups[dept_id]
        dept_name = dept_info['name']
        lines = sorted(dept_info['lines'], key=lambda l: (l.employee_name or ''))
        safe_dept_name = dept_name[:20]

        # --- XỬ LÝ SHEET TIỀN KPI ---
        ws_amount = wb.copy_worksheet(template_sheet_amount)
        ws_amount.title = f"Tiền KPI - {safe_dept_name}"
        ws_amount.sheet_properties.tabColor = "FF0000"
        
        # 1. Header (Sheet Tiền KPI)
        _fill_placeholder(ws_amount, 1, 1, {'company_name': company.name})
        _fill_placeholder(ws_amount, 2, 1, {'tax_number': company.vat or ''})
        _fill_placeholder(ws_amount, 3, 1, {'month': month_str, 'year': year_str})
        
        # Căn giữa ô A3
        ws_amount.merge_cells('A3:H3')
        ws_amount['A3'].alignment = Alignment(horizontal='center', vertical='center')
        
        # Ô A5: Bộ phận
        _fill_placeholder(ws_amount, 5, 1, {'department': dept_name})
        ws_amount.merge_cells('A5:B5')
        
        # 2. Điền dữ liệu nhân viên (Bắt đầu từ hàng 6 theo chuẩn template)
        # Bỏ insert_rows để tăng tốc độ
        data_row_start_amount = 6
        
        for i, line in enumerate(lines):
            row_idx = data_row_start_amount + i
            
            if i > 0:
                _copy_row_formatting(ws_amount, data_row_start_amount, row_idx, copy_value=False)
            
            # Ghi dữ liệu và công thức
            ws_amount.cell(row=row_idx, column=1, value=i + 1)
            ws_amount.cell(row=row_idx, column=2, value=line.employee_name or '')
            ws_amount.cell(row=row_idx, column=3, value=line.payroll_net_salary_base or 0)
            ws_amount.cell(row=row_idx, column=4, value=f'=IFERROR(C{row_idx}*E{row_idx},"-")')
            ws_amount.cell(row=row_idx, column=5, value=f'=+F{row_idx}-1')
            ws_amount.cell(row=row_idx, column=6, value=f'=1+(G{row_idx}-50)/50')
            
            # Điểm KPI với format 2 chữ số thập phân
            kpi_cell = ws_amount.cell(row=row_idx, column=7)
            kpi_cell.value = line.payroll_kpi_score or 0
            kpi_cell.number_format = '0.00'

        # 3. Footer (Ngày tháng năm)
        footer_date_row_amount = 6 + len(lines)
        _fill_placeholder(ws_amount, footer_date_row_amount, 4, {'last_day_of_month': last_day, 'month': month_str, 'year': year_str})

    # Xóa sheet mẫu
    wb.remove(template_sheet_point)
    wb.remove(template_sheet_amount)
    
    # Export
    output = io.BytesIO()
    wb.save(output)
    file_data = base64.b64encode(output.getvalue())
    output.close()
    
    return file_data, f"BAO_CAO_KPI_THANG_{month_str}_{year_str}.xlsx"
