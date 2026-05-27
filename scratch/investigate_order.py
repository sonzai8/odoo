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
    order = env['dl.wood.production.order'].search([('name', '=', 'QTP_SX_0526_0003')])
    if not order:
        print("Không tìm thấy lệnh sản xuất QTP_SX_0526_0003")
    else:
        print("Lệnh sản xuất:", order.name)
        print("Số lượng kế hoạch:", order.qty_planned)
        print("Tỷ lệ thu hồi cha (order.x_co_yield):", order.x_co_yield)
        
        print("\n--- CHI TIẾT VÁN BÓC (peeling_line_ids) ---")
        for line in order.peeling_line_ids:
            print(f"Dòng ID: {line.id}")
            print(f"  Tỷ lệ thu hồi dòng (line.x_co_yield): {line.x_co_yield}")
            print(f"  Tỷ lệ (x_ratio): {line.x_ratio}%")
            print(f"  KL KH (volume_planned): {line.volume_planned}")
            print(f"  KL TT (volume_actual): {line.volume_actual}")
