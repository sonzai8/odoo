from openpyxl import load_workbook
wb = load_workbook('/Users/sonzai/dev/odoo 19/odoo/my_custom_addons/dl_salary_kpi/static/src/templates/TEMPLATE_2026.xlsx')
ws = wb.active
for r in ws.merged_cells.ranges:
    print(r)
