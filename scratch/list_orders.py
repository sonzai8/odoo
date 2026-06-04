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
    print(f"Tìm thấy {len(orders)} lệnh sản xuất:")
    for order in orders:
        print(f"- Tên: {order.name}, Trạng thái: {order.state}, SL kế hoạch: {order.qty_planned}")
        print(f"  Định mức tổng thể: {order.x_total_ratio}%, Khai CO gỗ: {order.x_co_yield_wood}, Khai CO ván: {order.x_co_yield_peeling}")
