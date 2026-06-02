import re

file_path = '/Users/sonzai/dev/odoo 19/odoo/my_custom_addons/dl_wood_traceability/models/dl_wood_dossier_renderer.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace 'miningArea': d.x_area or 0.0,
content = re.sub(r'\'miningArea\':\s*d\.x_area\s*or\s*0\.0,', r'\'miningArea\': format_number_vn(d.x_area or 0.0, max_decimals=2),', content)

# Replace 'diameter_min': dia_min,
content = re.sub(r'\'diameter_min\':\s*dia_min,', r'\'diameter_min\': format_number_vn(dia_min, max_decimals=2),', content)

# Replace 'diameter_max': dia_max,
content = re.sub(r'\'diameter_max\':\s*dia_max,', r'\'diameter_max\': format_number_vn(dia_max, max_decimals=2),', content)

# Replace 'diametter_max': dia_max,
content = re.sub(r'\'diametter_max\':\s*dia_max,', r'\'diametter_max\': format_number_vn(dia_max, max_decimals=2),', content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done replacing.")
