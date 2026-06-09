import openpyxl
wb = openpyxl.Workbook()
ws = wb.active
for i in range(1, 10):
    ws.append([i, f"Name {i}"])

# Delete rows from bottom to top
rows_to_delete = [3, 5, 7] # 1-indexed in openpyxl
for r in reversed(rows_to_delete):
    ws.delete_rows(r)

for row in ws.iter_rows(values_only=True):
    print(row)
