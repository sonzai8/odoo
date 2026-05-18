import sys
sys.path.append('/Users/sonzai/dev/odoo 19/odoo')
import odoo
from odoo import api, tools

tools.config.parse_config(['-c', 'odoo.conf'])

registry = odoo.modules.registry.Registry('odoo_db')
with registry.cursor() as cr:
    env = api.Environment(cr, odoo.SUPERUSER_ID, {})
    
    print("=== ĐANG KHỞI CHẠY TÍNH TOÁN LẠI HỒ SƠ GỖ ===")
    dossiers = env['dl.wood.dossier'].search([])
    print(f"Tổng số hồ sơ gỗ cần cập nhật: {len(dossiers)}")
    
    for d in dossiers:
        print(f"-> Đang tính lại hồ sơ: {d.name} (ID: {d.id})")
        # Gọi lại hàm compute của Odoo để tính lại giá trị float 2 chữ số thập phân
        d._compute_initial_qty()
        d._compute_stock_quantities()
        
        # Lưu vào database
        d.write({
            'initial_qty': d.initial_qty,
            'initial_wood_qty': d.initial_wood_qty,
            'initial_firewood_qty': d.initial_firewood_qty,
            'remaining_qty': d.remaining_qty,
            'qty_reserved': d.qty_reserved,
            'qty_available': d.qty_available,
            'qty_consumed': d.qty_consumed
        })
        print(f"   + Ban đầu: {d.initial_qty}, Đã dùng: {d.qty_consumed}, Còn lại: {d.remaining_qty}")
        
    cr.commit()
    print("=== HOÀN THÀNH TÍNH TOÁN LẠI THÀNH CÔNG ===")
