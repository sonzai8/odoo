import sys
sys.path.append('/Users/sonzai/dev/odoo 19/odoo')
import odoo
from odoo import api, tools

tools.config.parse_config(['-c', 'odoo.conf'])

registry = odoo.modules.registry.Registry('odoo_db')
with registry.cursor() as cr:
    env = api.Environment(cr, odoo.SUPERUSER_ID, {})
    
    print("=== KIỂM TRA COMPANY CỦA SẢN PHẨM ===")
    wood_products = env['product.product'].search([('is_wood_product', '=', True)], limit=10)
    for p in wood_products:
        print(f"ID: {p.id}, Tên: {p.name[:50]}, Code: {p.default_code}, Display Name: {p.display_name}, Company: {p.company_id.name} (ID: {p.company_id.id if p.company_id else 'None'})")
        
    print("\n=== KIỂM TRA LỆNH SẢN XUẤT MỚI (DỰ THẢO) ===")
    # Lấy company_id mặc định của user 1 hoặc res.company
    company = env.company
    print(f"Company mặc định của session: {company.name} (ID: {company.id})")
