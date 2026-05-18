# -*- coding: utf-8 -*-
import sys

sys.path.append('/Users/sonzai/dev/odoo 19/odoo')
import odoo
from odoo import api, tools

tools.config.parse_config(['-c', 'odoo.conf'])

def test_sync_products():
    registry = odoo.modules.registry.Registry('odoo_db')
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        config = env['dl.woodpro.config'].search([], limit=1)
        if not config:
            print("Không tìm thấy cấu hình WoodPro nào!")
            return
            
        print("\n=== 1. KIỂM THỬ PHÂN TÍCH MÃ ĐẶC BIỆT ===")
        test_codes = [
            ("TPPK_M17.0-6105.840-A8", "Gỗ dán đặc biệt m3"),
            ("TPPK_T18.0-7-300 (X)", "Gỗ ván ép Tấm"),
            ("TPEPK_M11.0-10-6.7 (X)", "Gỗ ván ép Mét khối"),
            ("TPEPK_M11.0-A07", "Gỗ không có giá")
        ]
        
        for code, name in test_codes:
            thickness, width, length, thickness_alias, price, unit = config._parse_wood_product_specs(code, name)
            state = 'active' if price > 0 else 'inactive'
            print(f"Mã: {code}")
            print(f"  Độ dày: {thickness} mm")
            print(f"  Ký hiệu: {thickness_alias}")
            print(f"  Chiều dài: {length} mm | Chiều rộng: {width} mm")
            print(f"  Giá bán bóc tách: {price:,.0f} VND")
            print(f"  Đơn vị tính: {unit}")
            print(f"  Trạng thái kinh doanh dự kiến: {state}")
            print("-" * 50)
            
        print("\n=== 2. CHẠY ĐỒNG BỘ THỰC TẾ WOODPRO API ===")
        res = config.action_sync_products()
        print(f"Kết quả thông báo đồng bộ: {res}")
        
        # Truy vấn kiểm tra sản phẩm đặc biệt trong DB sau sync
        print("\n=== 3. TRUY VẤN KIỂM TRA SẢN PHẨM TRONG DATABASE ===")
        searched_codes = [tc[0] for tc in test_codes] + ["TPPK_M17.0-6105.840-A8"]
        products = env['product.template'].search([
            ('is_wood_product', '=', True),
            ('default_code', 'in', searched_codes)
        ])
        for p in products:
            print(f"Sản phẩm: {p.name}")
            print(f"  Mã (default_code): {p.default_code}")
            print(f"  Độ dày (x_thickness): {p.x_thickness} mm")
            print(f"  Chiều dài (x_length): {p.x_length} mm")
            print(f"  Chiều rộng (x_width): {p.x_width} mm")
            print(f"  Giá bán (list_price): {p.list_price:,.0f} VND")
            print(f"  Đơn vị (x_unit): {p.x_unit}")
            print(f"  UoM tiêu chuẩn: {p.uom_id.name}")
            print(f"  Trạng thái kinh doanh: {p.x_sale_state}")
            print("-" * 50)
            
        print("\n=== 4. KIỂM TRA MỘT SỐ SẢN PHẨM NGỪNG KINH DOANH ===")
        inactive_products = env['product.template'].search([
            ('is_wood_product', '=', True),
            ('x_sale_state', '=', 'inactive')
        ], limit=5)
        for p in inactive_products:
            print(f"Sản phẩm: {p.name}")
            print(f"  Mã (default_code): {p.default_code}")
            print(f"  Giá bán (list_price): {p.list_price:,.0f} VND")
            print(f"  Trạng thái kinh doanh: {p.x_sale_state}")
            print("-" * 50)

if __name__ == '__main__':
    test_sync_products()
