import sys
sys.path.append('/Users/sonzai/dev/odoo 19/odoo')
import odoo
from odoo import api, tools

tools.config.parse_config(['-c', 'odoo.conf'])

registry = odoo.modules.registry.Registry('odoo_db')
with registry.cursor() as cr:
    env = api.Environment(cr, odoo.SUPERUSER_ID, {})
    
    print("=== BẮT ĐẦU CHẠY THỬ NGHIỆM TỰ ĐỘNG GỢI Ý ĐỊNH MỨC DỰA TRÊN TỒN KHO ===")
    
    # 1. Tìm sản phẩm, loài gỗ, đối tác và các hồ sơ gỗ mẫu
    product = env['product.product'].search([('is_wood_product', '=', True)], limit=1)
    company = env.company
    species = env['dl.wood.species'].search([], limit=1)
    partner = env['res.partner'].search([], limit=1)
    
    if not product or not species or not partner:
        print("Lỗi: Cần ít nhất 1 sản phẩm gỗ, 1 loài gỗ và 1 đối tác hoạt động để chạy kiểm thử.")
        sys.exit(1)
        
    # Tạo 2 hồ sơ gỗ mẫu trong transaction để độc lập dữ liệu
    dossier_small = env['dl.wood.dossier'].create({
        'name': 'TEST_HS_SMALL',
        'company_id': company.id,
        'partner_id': partner.id,
        'state': 'draft',
        'line_ids': [(0, 0, {
            'species_id': species.id,
            'volume': 5.0,
            'price_unit': 1000000,
        })]
    })
    
    dossier_large = env['dl.wood.dossier'].create({
        'name': 'TEST_HS_LARGE',
        'company_id': company.id,
        'partner_id': partner.id,
        'state': 'draft',
        'line_ids': [(0, 0, {
            'species_id': species.id,
            'volume': 20.0,
            'price_unit': 1000000,
        })]
    })
    
    # Ép buộc tính toán lại các trường computed
    dossier_small._compute_initial_qty()
    dossier_small._compute_stock_quantities()
    dossier_large._compute_initial_qty()
    dossier_large._compute_stock_quantities()
    
    print(f"Hồ sơ nhỏ được tạo: {dossier_small.name} - Tồn kho khả dụng: {dossier_small.qty_available} m³")
    print(f"Hồ sơ lớn được tạo: {dossier_large.name} - Tồn kho khả dụng: {dossier_large.qty_available} m³")
    
    # 2. Tạo Lệnh sản xuất kế hoạch 10.0 m³ thành phẩm, Khai CO mặc định = 1.3
    # Tổng nguyên liệu gỗ cần thiết = 10.0 * 1.3 = 13.0 m³
    order = env['dl.wood.production.order'].create({
        'product_id': product.id,
        'qty_planned': 10.0,
        'qty_done': 10.0,
        'x_co_yield': 1.3,
        'company_id': company.id,
    })
    
    print(f"Tạo Lệnh sản xuất: SL kế hoạch = {order.qty_planned} m³, Khai CO mặc định = {order.x_co_yield}")
    print(f"  => Tổng lượng gỗ thô cần thiết: 13.00 m³")
    
    # 3. Thêm hồ sơ nhỏ làm dòng tiêu hao 1
    line1 = env['dl.wood.production.line'].new({
        'production_order_id': order.id,
        'dossier_id': dossier_small.id,
        'species_id': species.id,
    })
    line1._onchange_dossier_id()
    
    print("\n--- Thêm dòng tiêu hao thứ 1 (Hồ sơ nhỏ: 5.00 m³) ---")
    print(f"  + Khai CO của dòng 1: {line1.x_co_yield}")
    print(f"  + Định mức tự động gợi ý: {line1.x_ratio}% (Kỳ vọng: 38.46%)")
    
    # Đẩy line1 vào order.line_ids để tính toán tiếp
    order.write({
        'line_ids': [(0, 0, {
            'dossier_id': dossier_small.id,
            'species_id': species.id,
            'x_ratio': line1.x_ratio,
            'x_co_yield': line1.x_co_yield,
            'volume_planned': line1.volume_planned,
            'volume_actual': line1.volume_actual,
        })]
    })
    
    # Kiểm tra các trường tổng sau khi thêm dòng 1
    order._compute_total_volume()
    print(f"  => [CẬP NHẬT TỔNG] Tổng định mức hiện tại: {order.x_total_ratio}%")
    print(f"  => [CẬP NHẬT TỔNG] Định mức còn thiếu: {order.x_remaining_ratio}% (Kỳ vọng: 61.54%)")
    print(f"  => [CẬP NHẬT TỔNG] KL kế hoạch còn thiếu: {order.x_remaining_volume_planned} m³ (Kỳ vọng: 8.00)")
    
    # 4. Thêm hồ sơ lớn làm dòng tiêu hao 2
    line2 = env['dl.wood.production.line'].new({
        'production_order_id': order.id,
        'dossier_id': dossier_large.id,
        'species_id': species.id,
    })
    line2.production_order_id.line_ids = order.line_ids
    line2._onchange_dossier_id()
    
    print("\n--- Thêm dòng tiêu hao thứ 2 (Hồ sơ lớn: 20.00 m³) ---")
    print(f"  + Định mức tự động gợi ý: {line2.x_ratio}% (Kỳ vọng: 61.54%)")
    
    order.write({
        'line_ids': [(0, 0, {
            'dossier_id': dossier_large.id,
            'species_id': species.id,
            'x_ratio': line2.x_ratio,
            'x_co_yield': line2.x_co_yield,
            'volume_planned': line2.volume_planned,
            'volume_actual': line2.volume_actual,
        })]
    })
    
    order._compute_total_volume()
    print(f"  => [CẬP NHẬT TỔNG] Tổng định mức hiện tại: {order.x_total_ratio}% (Kỳ vọng: 100.00%)")
    print(f"  => [CẬP NHẬT TỔNG] Định mức còn thiếu: {order.x_remaining_ratio}% (Kỳ vọng: 0.00%)")
    print(f"  => [CẬP NHẬT TỔNG] KL kế hoạch còn thiếu: {order.x_remaining_volume_planned} m³ (Kỳ vọng: 0.00)")
    
    # Hủy giao dịch để bảo toàn dữ liệu gốc
    cr.rollback()
    print("\n=== HOÀN THÀNH KIỂM THỬ THÀNH CÔNG ===")
