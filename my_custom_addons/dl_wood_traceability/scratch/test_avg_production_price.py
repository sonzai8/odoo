# -*- coding: utf-8 -*-
import os
import sys

# Thêm đường dẫn Odoo vào python path
sys.path.append('/Users/sonzai/dev/odoo 19/odoo')

import odoo
from odoo import api, tools

tools.config.parse_config(['-c', 'odoo.conf'])

def test_avg_production_price():
    # Khởi tạo registry Odoo
    reg = odoo.modules.registry.Registry('odoo_db')
    with reg.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        # 1. Tìm hoặc tạo loài gỗ mẫu
        species = env['dl.wood.species'].search([], limit=1)
        if not species:
            species = env['dl.wood.species'].create({
                'name': 'Gỗ Thông Test Price',
                'wood_type': 'wood',
            })
            
        # 2. Tạo Hồ sơ gỗ mẫu có giá cụ thể
        partner = env['res.partner'].search([], limit=1)
        dossier = env['dl.wood.dossier'].create({
            'name': 'HS-TEST-PRICE-001',
            'partner_id': partner.id if partner else False,
            'initial_qty': 100.0,
            'remaining_qty': 100.0,
        })
        
        # Tạo dòng chi tiết hồ sơ gỗ với đơn giá là 5,000,000 VND / m³
        dossier_line = env['dl.wood.dossier.line'].create({
            'dossier_id': dossier.id,
            'species_id': species.id,
            'volume': 50,
            'price_unit': 5000000, # 5 triệu / m3
        })
        print(f"-> Đã tạo Hồ sơ gỗ: {dossier.name} có đơn giá gỗ {species.name} là: {dossier_line.price_unit} VND/m³")
        
        # 3. Tìm hoặc tạo sản phẩm gỗ thành phẩm có thông số thể tích
        product = env['product.product'].search([('is_wood_product', '=', True), ('x_volume_m3', '>', 0)], limit=1)
        if not product:
            product = env['product.product'].create({
                'name': 'Ván gỗ thành phẩm Test 18mm',
                'is_wood_product': True,
                'default_code': 'TEST_VAN_18',
                'x_length': 2440.0,
                'x_width': 1220.0,
                'x_thickness': 18.0,
                'x_volume_m3': 0.05,
            })
        
        vol_per_unit = product.x_volume_m3
        print(f"-> Sản phẩm sản xuất: {product.display_name} - Thể tích đơn vị: {vol_per_unit} m³")
        
        # 4. Tạo Lệnh sản xuất ở dạng Dự thảo (draft)
        order = env['dl.wood.production.order'].create({
            'name': 'LSX-TEST-PRICE',
            'product_id': product.id,
            'qty_planned': 10.0, # Lập kế hoạch 10 tấm thành phẩm
            'qty_done': 0.0, # Chưa sản xuất
            'x_co_yield': 1.3,
            'state': 'draft',
        })
        print(f"-> Tạo Lệnh sản xuất: {order.name} ở trạng thái: {order.state}")
        
        # 5. Tạo dòng tiêu hao nguyên vật liệu gỗ
        # Tiêu hao 13.0 m3 kế hoạch (tương đương 100% định mức gỗ cho 10 tấm thành phẩm)
        line = env['dl.wood.production.line'].create({
            'production_order_id': order.id,
            'dossier_id': dossier.id,
            'species_id': species.id,
            'x_ratio': 100.0,
            'x_co_yield': 1.3,
            'volume_planned': 13.0,
            'volume_actual': 0.0,
        })
        
        # Trigger các hàm compute để cập nhật chi phí
        line._compute_x_price_unit()
        line._compute_x_subtotal_cost()
        order._compute_production_costs()
        
        # KIỂM TRA 1: Trong trạng thái DỰ THẢO (Dự kiến)
        print("\n--- KIỂM TRA TRẠNG THÁI DỰ THẢO (ƯỚC TÍNH CHI PHÍ) ---")
        print(f"Đơn giá dòng tiêu hao: {line.x_price_unit} VND (Mong đợi: 5,000,000)")
        print(f"Thành tiền dòng tiêu hao (Planned Volume 13.0 m3 * Đơn giá 5tr): {line.x_subtotal_cost} VND (Mong đợi: 65,000,000)")
        print(f"Tổng tiền gỗ Lệnh sản xuất: {order.x_total_wood_cost} VND (Mong đợi: 65,000,000)")
        
        # Tổng thể tích thành phẩm dự kiến = 10.0 * vol_per_unit
        expected_finished_vol = 10.0 * vol_per_unit
        # Giá sản xuất trung bình dự kiến = 65,000,000 / expected_finished_vol
        expected_avg_price = round(65000000.0 / expected_finished_vol, 2) if expected_finished_vol > 0 else 6500000.0
        print(f"Thể tích thành phẩm dự kiến: {expected_finished_vol} m³")
        print(f"Giá sản xuất trung bình dự kiến: {order.x_avg_production_price} VND/m³ thành phẩm (Mong đợi: {expected_avg_price})")
        
        assert line.x_price_unit == 5000000.0, "Đơn giá dòng tiêu hao sai lệch!"
        assert line.x_subtotal_cost == 65000000.0, "Thành tiền dòng tiêu hao dự kiến sai lệch!"
        assert order.x_total_wood_cost == 65000000.0, "Tổng chi phí gỗ dự kiến sai lệch!"
        if expected_finished_vol > 0:
            assert abs(order.x_avg_production_price - expected_avg_price) < 0.1, "Giá sản xuất trung bình dự kiến sai lệch!"
            
        print("\n--- CHI TIẾT GIẢI THÍCH HTML (DỰ THẢO) ---")
        print(order.x_avg_production_price_explanation)
        
        # KIỂM TRA 2: BẮT ĐẦU SẢN XUẤT (IN PROGRESS)
        print("\n--- KIỂM TRA TRẠNG THÁI ĐANG SẢN XUẤT (THỰC TẾ CHI PHÍ) ---")
        order.action_start()
        # Thiết lập số lượng sản xuất thực tế là 8.0 tấm thành phẩm
        order.qty_done = 8.0
        # Thiết lập khối lượng thực tế tiêu hao gỗ là 10.4 m3
        line.volume_actual = 10.4
        
        # Trigger compute
        line._compute_x_subtotal_cost()
        order._compute_production_costs()
        
        print(f"Trạng thái Lệnh SX: {order.state}")
        print(f"Thành tiền dòng tiêu hao thực tế (Actual Volume 10.4 m3 * Đơn giá 5tr): {line.x_subtotal_cost} VND (Mong đợi: 52,000,000)")
        print(f"Tổng tiền gỗ thực tế: {order.x_total_wood_cost} VND (Mong đợi: 52,000,000)")
        
        # Tổng thể tích thành phẩm thực tế = 8.0 * vol_per_unit
        expected_actual_finished_vol = 8.0 * vol_per_unit
        expected_actual_avg_price = round(52000000.0 / expected_actual_finished_vol, 2) if expected_actual_finished_vol > 0 else 6500000.0
        print(f"Thể tích thành phẩm thực tế: {expected_actual_finished_vol} m³")
        print(f"Giá sản xuất trung bình thực tế: {order.x_avg_production_price} VND/m³ thành phẩm (Mong đợi: {expected_actual_avg_price})")
        
        assert line.x_subtotal_cost == 52000000.0, "Thành tiền dòng tiêu hao thực tế sai lệch!"
        assert order.x_total_wood_cost == 52000000.0, "Tổng chi phí gỗ thực tế sai lệch!"
        if expected_actual_finished_vol > 0:
            assert abs(order.x_avg_production_price - expected_actual_avg_price) < 0.1, "Giá sản xuất trung bình thực tế sai lệch!"
            
        print("\n--- CHI TIẾT GIẢI THÍCH HTML (ĐANG SẢN XUẤT) ---")
        print(order.x_avg_production_price_explanation)
            
        # 6. Dọn dẹp dữ liệu để không tạo rác DB
        order.unlink()
        dossier.unlink()
        print("\n=== KIỂM THỬ TẤT CẢ ĐỀU ĐẠT 100% ===")

if __name__ == '__main__':
    test_avg_production_price()
