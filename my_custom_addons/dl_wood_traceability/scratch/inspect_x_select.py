import sys
sys.path.append('/Users/sonzai/dev/odoo 19/odoo')
import odoo
from odoo import api, tools

tools.config.parse_config(['-c', 'odoo.conf'])

registry = odoo.modules.registry.Registry('odoo_db')
with registry.cursor() as cr:
    env = api.Environment(cr, odoo.SUPERUSER_ID, {})
    
    print("=== INSPECTING PRODUCTION ORDERS ===")
    prods = env['dl.wood.production.order'].search([], order='id desc', limit=5)
    for p in prods:
        print(f"Prod ID: {p.id}, name: {p.name}, sale_order_id: {p.sale_order_id.id if p.sale_order_id else None}, x_select_production_id: {p.x_select_production_id.id if p.x_select_production_id else None}")
