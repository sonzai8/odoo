with open('/Users/sonzai/dev/odoo 19/odoo/my_custom_addons/dl_wood_traceability/models/dl_wood_production.py', 'r') as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    line_num = idx + 1
    if 'x_co_yield' in line:
        print(f"L{line_num}: {line.strip()}")
