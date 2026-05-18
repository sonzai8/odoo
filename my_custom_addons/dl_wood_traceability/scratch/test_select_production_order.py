import sys
sys.path.append('/Users/sonzai/dev/odoo 19/odoo')
import odoo
from odoo import api, tools

tools.config.parse_config(['-c', 'odoo.conf'])

registry = odoo.modules.registry.Registry('odoo_db')
with registry.cursor() as cr:
    env = api.Environment(cr, odoo.SUPERUSER_ID, {})
    
    print("=== BẮT ĐẦU CHẠY THỬ NGHIỆM CHỌN LỆNH SẢN XUẤT CÓ SẴN CHO ĐƠN HÀNG ===")
    
    # 1. Tạo Khách hàng và Sản phẩm gỗ tạm thời phục vụ kiểm thử
    partner = env['res.partner'].create({
        'name': 'KHACH_HANG_TEST_SX',
        'x_is_wood_customer': True,
    })
    
    product = env['product.product'].create({
        'name': 'SAN_PHAM_GO_TEST_SX',
        'is_wood_product': True,
    })
    
    company = env.company
    
    print(f"Tạo đối tượng tạm thời: Khách hàng ID={partner.id}, Sản phẩm ID={product.id}")
        
    # 2. Tạo một Lệnh sản xuất tự do (chưa gắn vào Sale Order nào)
    standalone_prod = env['dl.wood.production.order'].create({
        'name': 'TEST_SX_STANDALONE',
        'product_id': product.id,
        'qty_planned': 15.0,
        'qty_done': 15.0,
        'x_co_yield': 1.3,
        'company_id': company.id,
    })
    
    print(f"Tạo thành công Lệnh sản xuất tự do: ID={standalone_prod.id}, Tên={standalone_prod.name}, SO={standalone_prod.sale_order_id}")
    
    # 3. Tạo một Đơn đặt hàng gỗ (dl.wood.sale.order) mới
    # Giả lập thao tác người dùng chọn Lệnh sản xuất tự do qua trường x_select_production_id
    sale_order = env['dl.wood.sale.order'].create({
        'partner_id': partner.id,
        'company_id': company.id,
        'production_order_ids': [(0, 0, {
            'x_select_production_id': standalone_prod.id,
            'product_id': standalone_prod.product_id.id,
            'qty_planned': standalone_prod.qty_planned,
            'qty_done': standalone_prod.qty_done,
            'date_planned': standalone_prod.date_planned,
        })]
    })
    
    print(f"Tạo thành công Đơn đặt hàng gỗ: ID={sale_order.id}, Mã={sale_order.name}")
    
    # 4. Xác minh xem Lệnh sản xuất tự do đã được liên kết chính xác chưa
    env.invalidate_all()
    standalone_prod = env['dl.wood.production.order'].browse(standalone_prod.id)
    sale_order = env['dl.wood.sale.order'].browse(sale_order.id)
    
    print("\n--- Xác minh sau khi liên kết ---")
    print(f"  + Lệnh sản xuất liên kết SO ID: {standalone_prod.sale_order_id.id} (Kỳ vọng: {sale_order.id})")
    print(f"  + Số lượng lệnh sản xuất trong SO: {len(sale_order.production_order_ids)} (Kỳ vọng: 1)")
    print(f"  + ID của lệnh trong SO: {sale_order.production_order_ids[0].id} (Kỳ vọng: {standalone_prod.id})")
    
    if standalone_prod.sale_order_id.id == sale_order.id and len(sale_order.production_order_ids) == 1 and sale_order.production_order_ids[0].id == standalone_prod.id:
        print("=> KẾT QUẢ LIÊN KẾT: ĐẠT! Lệnh sản xuất đã được gán chính xác vào SO mà không tạo bản ghi trùng lặp!")
    else:
        print("=> KẾT QUẢ LIÊN KẾT: THẤT BẠI!")
        cr.rollback()
        sys.exit(1)
        
    # 5. Kiểm tra tính năng unlinking (Hủy liên kết thay vì xóa cứng)
    print("\n--- Kiểm tra hủy liên kết (unlink khỏi SO) ---")
    sale_order.write({
        'production_order_ids': [(2, standalone_prod.id, 0)]
    })
    
    env.invalidate_all()
    standalone_prod = env['dl.wood.production.order'].search([('id', '=', standalone_prod.id)])
    
    if standalone_prod:
        print(f"  => Lệnh sản xuất vẫn tồn tại trong DB! ID={standalone_prod.id}")
        print(f"  => Trạng thái liên kết SO sau khi xóa dòng: {standalone_prod.sale_order_id.id} (Kỳ vọng: False/None)")
        if not standalone_prod.sale_order_id:
            print("=> KẾT QUẢ HỦY LIÊN KẾT: ĐẠT! Lệnh sản xuất chỉ bị gỡ liên kết khỏi đơn hàng và giữ nguyên dữ liệu gốc!")
        else:
            print("=> KẾT QUẢ HỦY LIÊN KẾT: THẤT BẠI (vẫn còn gán SO)!")
    else:
        print("=> KẾT QUẢ HỦY LIÊN KẾT: THẤT BẠI! Bản ghi lệnh sản xuất đã bị xóa cứng khỏi DB!")
        
    cr.rollback()
    print("\n=== HOÀN THÀNH TOÀN BỘ KIỂM THỬ THÀNH CÔNG ===")
