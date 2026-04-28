import sys
from openpyxl import load_workbook
import copy
from openpyxl.cell.cell import MergedCell
from openpyxl.formula.translate import Translator

def safe_write(ws, row, col, value):
    cell = ws.cell(row=row, column=col)
    if isinstance(cell, MergedCell):
        return
    cell.value = value

print("Loading workbook...")
wb = load_workbook('/Users/sonzai/dev/odoo 19/odoo/my_custom_addons/dl_salary_kpi/static/src/templates/TEMPLATE_2026.xlsx')
wb.calculation.fullCalcOnLoad = True
ws = wb.active
ws.title = "Tháng 01 - năm 2025"

# 1. Header
safe_write(ws, 3, 1, "Tháng 01 năm 2025")
safe_write(ws, 4, 7, 100000000.0)
safe_write(ws, 4, 11, 1)
safe_write(ws, 4, 15, 2025)

# 2. Data
for current_row in range(8, 15):
    if current_row > 8:
        for source_cell in ws[8]:
            target_cell = ws.cell(row=current_row, column=source_cell.column)
            if source_cell.data_type == 'f':
                formula = source_cell.value
                try:
                    target_cell.value = Translator(formula, source_cell.coordinate).translate_formula(target_cell.coordinate)
                except Exception:
                    target_cell.value = formula
            else:
                target_cell.value = source_cell.value

            if source_cell.has_style:
                target_cell.font = copy.copy(source_cell.font)
                target_cell.border = copy.copy(source_cell.border)
                target_cell.fill = copy.copy(source_cell.fill)
                target_cell.number_format = source_cell.number_format
                target_cell.protection = copy.copy(source_cell.protection)
                target_cell.alignment = copy.copy(source_cell.alignment)
        
        if ws.row_dimensions[8].height:
            ws.row_dimensions[current_row].height = ws.row_dimensions[8].height

    # Mapping
    safe_write(ws, current_row, 1, current_row - 7)
    safe_write(ws, current_row, 2, '0123456789')
    safe_write(ws, current_row, 3, 'Nguyen Van A')
    safe_write(ws, current_row, 4, '01/01/1990')
    safe_write(ws, current_row, 5, '012345678912')
    safe_write(ws, current_row, 6, 'Nam')
    safe_write(ws, current_row, 7, 'Phòng Kế toán')
    safe_write(ws, current_row, 8, 'Nhân viên')
    safe_write(ws, current_row, 9, 10000000)

    for day in range(1, 32):
        col_idx = 9 + day
        safe_write(ws, current_row, col_idx, 'N')

    safe_write(ws, current_row, 95, 0.0)
    safe_write(ws, current_row, 96, 650000.0)
    safe_write(ws, current_row, 111, None)
    safe_write(ws, current_row, 135, 0.0)
    safe_write(ws, current_row, 138, 2)

wb.save('test_corrupt_output.xlsx')
print("Saved to test_corrupt_output.xlsx")
