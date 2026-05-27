import os
import sys

# Thêm đường dẫn project vào sys.path
sys.path.append('/Users/sonzai/dev/odoo 19/odoo')

import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

# Khởi tạo cấu hình Odoo
odoo.tools.config.parse_config(['-c', 'odoo.conf'])
registry = Registry('odoo_db_production')

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    dossier = env['dl.wood.peeling.dossier'].search([('name', '=', 'QTP_HSV_0003')])
    if not dossier:
        print("Không tìm thấy hồ sơ ván bóc QTP_HSV_0003")
    else:
        print("Hồ sơ ván bóc:", dossier.name)
        print("Tổng khối lượng ban đầu (qty_initial):", dossier.qty_initial)
        print("Tổng khối lượng đã dùng (qty_used):", dossier.qty_used)
        print("Tổng tồn khả dụng (qty_available):", dossier.qty_available)
        
        print("\n--- CHI TIẾT HÓA ĐƠN LIÊN KẾT (invoice_ids) ---")
        for inv in dossier.invoice_ids:
            print(f"HĐ số: {inv.invoice_number}, Trạng thái: {inv.state}, Ban đầu: {inv.qty_initial}, Đã dùng: {inv.qty_used}, Khả dụng: {inv.qty_available}")
