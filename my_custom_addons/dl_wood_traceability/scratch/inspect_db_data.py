import sys
import os

# Giả lập Odoo environment
sys.path.append('/Users/sonzai/dev/odoo 19/odoo')
import odoo
from odoo import api, tools

tools.config.parse_config(['-c', 'odoo.conf'])

registry = odoo.modules.registry.Registry('odoo_db')
with registry.cursor() as cr:
    env = api.Environment(cr, odoo.SUPERUSER_ID, {})
    
    print("=== KIỂM TRA SẢN PHẨM ===")
    products = env['product.product'].search([])
    print(f"Tổng số product.product trong DB: {len(products)}")
    
    wood_products = env['product.product'].search([('is_wood_product', '=', True)])
    print(f"Số sản phẩm có is_wood_product = True: {len(wood_products)}")
    for p in wood_products:
        print(f"  - ID: {p.id}, Tên: {p.name}")
        
    print("\n=== KIỂM TRA HỒ SƠ GỖ ===")
    dossiers = env['dl.wood.dossier'].search([])
    print(f"Tổng số hồ sơ gỗ: {len(dossiers)}")
    for d in dossiers[:5]:
        print(f"  - ID: {d.id}, Mã hồ sơ: {d.name}, Công ty: {d.company_id.name}, Trạng thái: {d.state}")
        for line in d.line_ids:
            print(f"    + Loài gỗ: {line.species_id.name} (ID: {line.species_id.id}), KL: {line.volume} m³")
            
    print("\n=== KIỂM TRA LỆNH SẢN XUẤT ===")
    orders = env['dl.wood.production.order'].search([], limit=3)
    for o in orders:
        print(f"  - Lệnh SX: {o.name}, Sản phẩm: {o.product_id.name if o.product_id else 'Chưa chọn'}, KL thực tế: {o.qty_done}")
