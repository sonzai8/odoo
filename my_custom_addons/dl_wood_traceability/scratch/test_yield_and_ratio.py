import sys
sys.path.append('/Users/sonzai/dev/odoo 19/odoo')
import odoo
from odoo import api, tools
from odoo.exceptions import ValidationError

tools.config.parse_config(['-c', 'odoo.conf'])

registry = odoo.modules.registry.Registry('odoo_db')
with registry.cursor() as cr:
    env = api.Environment(cr, odoo.SUPERUSER_ID, {})
    
    print("=== BẮT ĐẦU CHẠY THỬ NGHIỆM ĐỊNH MỨC & KHAI CO CẤP DÒNG ===")
    
    # 1. Tìm hoặc tạo sản phẩm gỗ mẫu và công ty
    product = env['product.product'].search([('is_wood_product', '=', True)], limit=1)
    company = env.company
    species = env['dl.wood.species'].search([], limit=1)
    dossier = env['dl.wood.dossier'].search([('state', '!=', 'cancelled')], limit=1)
    
    if not product or not species or not dossier:
        print("Lỗi: Không tìm thấy dữ liệu mẫu đầy đủ để kiểm thử.")
        sys.exit(1)
        
    print(f"Sản phẩm sử dụng: {product.name} (ID: {product.id})")
    print(f"Hồ sơ gỗ nguồn: {dossier.name} (ID: {dossier.id})")
    print(f"Loài gỗ: {species.name} (ID: {species.id})")
    
    # 2. Tạo Lệnh sản xuất nháp
    order = env['dl.wood.production.order'].create({
        'product_id': product.id,
        'qty_planned': 10.0,
        'qty_done': 10.0,
        'company_id': company.id,
    })
    
    print(f"Lệnh sản xuất nháp được tạo: {order.name} (ID: {order.id})")
    print(f"  + Giá trị mặc định Khai CO mặc định trên Order: {order.x_co_yield} (Kỳ vọng: 1.3)")
    
    # 3. Thay đổi Khai CO mặc định trên Order thành 1.4
    order.x_co_yield = 1.4
    print(f"  + Thay đổi Khai CO mặc định trên Order thành: {order.x_co_yield}")
    
    # 4. Thêm dòng tiêu hao 1: Định mức 40.0%
    line1 = env['dl.wood.production.line'].create({
        'production_order_id': order.id,
        'dossier_id': dossier.id,
        'species_id': species.id,
        'x_ratio': 40.0,
    })
    
    # Kích hoạt onchange để lấy Khai CO mặc định từ order
    line1._onchange_dossier_id()
    print(f"  + Thêm dòng 1: Khai CO của dòng tự động lấy từ Order = {line1.x_co_yield} (Kỳ vọng: 1.4)")
    
    line1._onchange_ratio_and_co()
    print(f"  + KL Kế hoạch tính ra (40% định mức, 1.4 Khai CO) = {line1.volume_planned} m³ (Kỳ vọng: 5.60)")
    
    # 5. Tùy chỉnh Khai CO của riêng dòng 1 thành 1.5
    line1.x_co_yield = 1.5
    line1._onchange_ratio_and_co()
    print(f"  + Thay đổi Khai CO của riêng dòng 1 thành 1.5: KL Kế hoạch mới = {line1.volume_planned} m³ (Kỳ vọng: 6.00)")
    
    # 6. Thêm dòng tiêu hao 2: Định mức 60.0%, giữ nguyên Khai CO = 1.4
    line2 = env['dl.wood.production.line'].create({
        'production_order_id': order.id,
        'dossier_id': dossier.id,
        'species_id': species.id,
        'x_ratio': 60.0,
    })
    line2._onchange_dossier_id()
    line2._onchange_ratio_and_co()
    print(f"  + Thêm dòng 2 (60% định mức, 1.4 Khai CO): KL Kế hoạch = {line2.volume_planned} m³ (Kỳ vọng: 8.40)")
    
    # 7. Kiểm tra đồng bộ hàng loạt từ Order
    print("  + Kiểm tra đồng bộ hàng loạt từ Order: Thay đổi Khai CO mặc định trên Order thành 2.0...")
    order.x_co_yield = 2.0
    order._onchange_x_co_yield()
    print(f"    => Khai CO trên dòng 1: {line1.x_co_yield} (Kỳ vọng: 2.0)")
    print(f"    => KL Kế hoạch dòng 1 (40%): {line1.volume_planned} m³ (Kỳ vọng: 8.00)")
    print(f"    => Khai CO trên dòng 2: {line2.x_co_yield} (Kỳ vọng: 2.0)")
    print(f"    => KL Kế hoạch dòng 2 (60%): {line2.volume_planned} m³ (Kỳ vọng: 12.00)")
    
    # 8. Thử nghiệm trạng thái và ràng buộc 100%
    print("  + Kiểm tra ràng buộc tổng định mức = 100% khi chuyển trạng thái sang Đang sản xuất...")
    order.state = 'in_progress'
    try:
        order._check_ratios_total()
        print("    => ĐẠT: Xác nhận thành công khi tổng định mức = 100%!")
    except ValidationError as e:
        print(f"    => THẤT BẠI: Lỗi không đáng có: {e}")
        
    # 9. Thử nghiệm ràng buộc khi tổng định mức khác 100%
    print("  + Đổi định mức dòng 1 sang 30% (Tổng định mức = 90.0%)...")
    line1.x_ratio = 30.0
    try:
        order._check_ratios_total()
        print("    => THẤT BẠI: Hệ thống không chặn lỗi khi tổng định mức không bằng 100%!")
    except ValidationError as e:
        print(f"    => ĐẠT: Hệ thống đã chặn thành công và ném lỗi ValidationError: {e}")
        
    # Hủy transaction để không lưu rác vào DB
    cr.rollback()
    print("=== HOÀN THÀNH CHẠY THỬ NGHIỆM THÀNH CÔNG ===")
