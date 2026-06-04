import re

file_path = '/Users/sonzai/dev/odoo 19/odoo/my_custom_addons/dl_wood_traceability/models/dl_wood_dossier_renderer.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern 1: format_volume_vietnamese(X) -> format_number_vn(X)
content = content.replace('format_volume_vietnamese(', 'format_number_vn(')

# Pattern 2: f"{int(round(X)):,}".replace(',', '.') -> format_number_vn(X, max_decimals=0)
content = re.sub(r'f"\{int\(round\(([^)]+)\)\):,\}"\.replace\([\'"],[\'"],\s*[\'"]\.[\'"]\)', r'format_number_vn(\1, max_decimals=0)', content)

# Pattern 3: f"{int(X):,}".replace(',', '.') -> format_number_vn(X, max_decimals=0)
content = re.sub(r'f"\{int\(([^)]+)\):,\}"\.replace\([\'"],[\'"],\s*[\'"]\.[\'"]\)', r'format_number_vn(\1, max_decimals=0)', content)

# Pattern 4: f"{X:.2f}".replace('.', ',') -> format_number_vn(X, max_decimals=2)
content = re.sub(r'f"\{([^:]+):\.2f\}"\.replace\([\'"]\.[\'"],\s*[\'"],[\'"]\)', r'format_number_vn(\1, max_decimals=2)', content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done replacing.")
