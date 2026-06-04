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
    orders = env['dl.wood.production.order'].search([])
    for order in orders:
        print(f"Trước recompute - {order.name}:")
        print(f"  wood_ratio: {order.x_wood_ratio} (remaining: {order.x_wood_remaining_ratio})")
        print(f"  peeling_ratio: {order.x_peeling_ratio} (remaining: {order.x_peeling_remaining_ratio})")
        print(f"  total_ratio: {order.x_total_ratio} (remaining: {order.x_remaining_ratio})")
        
        # Trigger compute
        order._compute_total_volume()
        
        print(f"Sau recompute - {order.name}:")
        print(f"  wood_ratio: {order.x_wood_ratio} (remaining: {order.x_wood_remaining_ratio})")
        print(f"  peeling_ratio: {order.x_peeling_ratio} (remaining: {order.x_peeling_remaining_ratio})")
        print(f"  total_ratio: {order.x_total_ratio} (remaining: {order.x_remaining_ratio})")
        print("--------------------")
