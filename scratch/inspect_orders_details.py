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
    orders = env['dl.wood.production.order'].search([], limit=10)
    for order in orders:
        print("====================================")
        print(f"Lệnh sản xuất: {order.name}")
        print(f"Trạng thái: {order.state}")
        print(f"Sản phẩm: {order.product_id.name}")
        print(f"Định mức tổng thể: {order.x_total_ratio}%")
        print(f"Định mức gỗ: {order.x_wood_ratio}% (Còn thiếu: {order.x_wood_remaining_ratio}%)")
        print(f"Định mức ván: {order.x_peeling_ratio}% (Còn thiếu: {order.x_peeling_remaining_ratio}%)")
        print(f"Tỷ lệ CO gỗ: {order.x_co_yield_wood}, Tỷ lệ CO ván: {order.x_co_yield_peeling}")
        
        print("\n--- CHI TIẾT GỖ (line_ids) ---")
        for line in order.line_ids:
            print(f"- Hồ sơ: {line.dossier_id.name}, Tồn KD: {line.x_qty_available}, Định mức: {line.x_ratio}%, Khai CO: {line.x_co_yield}, KL KH: {line.volume_planned}, KL TT: {line.volume_actual}")
            
        print("\n--- CHI TIẾT VÁN BÓC (peeling_line_ids) ---")
        for line in order.peeling_line_ids:
            print(f"- Hồ sơ: {line.peeling_dossier_id.name}, Tồn KD: {line.x_qty_available}, Định mức: {line.x_ratio}%, Khai CO: {line.x_co_yield}, KL KH: {line.volume_planned}, KL TT: {line.volume_actual}")
        print("\n")
