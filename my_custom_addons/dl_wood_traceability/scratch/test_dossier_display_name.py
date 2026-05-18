import sys
sys.path.append('/Users/sonzai/dev/odoo 19/odoo')
import odoo
from odoo import api, tools

tools.config.parse_config(['-c', 'odoo.conf'])

registry = odoo.modules.registry.Registry('odoo_db')
with registry.cursor() as cr:
    env = api.Environment(cr, odoo.SUPERUSER_ID, {})
    
    print("=== BẮT ĐẦU CHẠY THỬ NGHIỆM TÊN HIỂN THỊ HỒ SƠ GỖ ===")
    
    # Tìm hồ sơ gỗ bất kỳ trong hệ thống
    dossier = env['dl.wood.dossier'].search([('state', '!=', 'cancelled')], limit=1)
    
    if not dossier:
        print("Lỗi: Không tìm thấy hồ sơ gỗ nào để kiểm thử.")
        sys.exit(1)
        
    print(f"Hồ sơ được tìm thấy: ID={dossier.id}")
    print(f"  + Mã hồ sơ (name): {dossier.name}")
    print(f"  + Chủ rừng (partner_id): {dossier.partner_id.name}")
    print(f"  + Tồn kho khả dụng (qty_available): {dossier.qty_available} m³")
    print(f"  => Tên hiển thị thực tế (display_name): {dossier.display_name}")
    
    # Kiểm thử tính đúng đắn của định dạng
    expected_name = f"{dossier.name} - {dossier.partner_id.name or 'Không có chủ rừng'} - {dossier.qty_available:.2f} m³"
    if dossier.display_name == expected_name:
        print("\n=> KẾT QUẢ: ĐẠT! Tên hiển thị khớp 100% định dạng yêu cầu!")
    else:
        print(f"\n=> KẾT QUẢ: THẤT BẠI!\n  - Mong muốn: {expected_name}\n  - Thực tế:  {dossier.display_name}")
        
    cr.rollback()
    print("=== HOÀN THÀNH CHẠY THỬ NGHIỆM THÀNH CÔNG ===")
