import re

file_path = '/Users/sonzai/dev/odoo 19/odoo/my_custom_addons/dl_wood_traceability/models/dl_wood_dossier_renderer.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(r"\'miningArea\':", "'miningArea':")
content = content.replace(r"\'diameter_min\':", "'diameter_min':")
content = content.replace(r"\'diameter_max\':", "'diameter_max':")
content = content.replace(r"\'diametter_max\':", "'diametter_max':")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done fixing.")
