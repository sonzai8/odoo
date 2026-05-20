# -*- coding: utf-8 -*-
"""
Kịch bản kiểm thử tích hợp tự động cho chức năng Kiểm kê & Rollback Hồ Sơ Gỗ.
Cách chạy: python3 odoo-bin -c odoo.conf -d odoo_db --shell < my_custom_addons/dl_wood_traceability/scratch/test_dossier_stocktaking.py
"""
import sys
from odoo import fields

print("======================================================================")
print("BẮT ĐẦU CHẠY KIỂM THỬ TỰ ĐỘNG CHỨC NĂNG KIỂM KÊ & ROLLBACK HỒ SƠ GỖ")
print("======================================================================")

# Khởi tạo môi trường Odoo shell
env = self.env
company = env.company
partner = env['res.partner'].search([], limit=1)
if not partner:
    partner = env['res.partner'].create({'name': 'Khách hàng Test Kiểm Kê'})

# 1. Tìm hoặc tạo một loài gỗ Test
species = env['dl.wood.species'].search([('name', '=', 'Keo Lai Test KK')], limit=1)
if not species:
    species = env['dl.wood.species'].create({
        'name': 'Keo Lai Test KK',
        'code': 'KL_TEST_KK',
        'wood_type': 'wood',
        'company_id': company.id,
    })
print(f"-> Sử dụng Loài gỗ: {species.name} [ID: {species.id}]")

# 2. Tạo một hồ sơ gỗ Test với 100 m3 ban đầu
dossier = env['dl.wood.dossier'].create({
    'partner_id': partner.id,
    'company_id': company.id,
    'line_ids': [(0, 0, {
        'species_id': species.id,
        'volume': 100.0,
        'quantity': 10,
    })]
})
dossier._compute_initial_qty()
dossier._compute_stock_quantities()
print(f"-> Đã tạo Hồ sơ gỗ Test: {dossier.name} [ID: {dossier.id}]")
print(f"   + Khối lượng ban đầu: {dossier.initial_qty} m³")
print(f"   + Tồn kho thực tế hiện tại: {dossier.remaining_qty} m³")

assert dossier.remaining_qty == 100.0, "LỖI: Tồn kho ban đầu không chính xác!"

# 3. Tạo phiếu kiểm kê nháp
inventory = env['dl.wood.dossier.inventory'].create({
    'company_id': company.id,
    'date': fields.Date.today(),
    'note': 'Rà soát hao hụt cuối tháng test',
})
print(f"-> Đã tạo Phiếu kiểm kê nháp: {inventory.name} [ID: {inventory.id}]")

# 4. Gắn dossier vào phiếu và kích hoạt Onchange nạp dòng tự động (Auto-load)
inventory.write({'dossier_ids': [(6, 0, [dossier.id])]})
inventory._onchange_dossier_ids()
print(f"-> Đã chạy Auto-load dòng chi tiết. Số dòng được nạp: {len(inventory.line_ids)}")

assert len(inventory.line_ids) == 1, "LỖI: Không tự động nạp được loài gỗ từ hồ sơ!"
line = inventory.line_ids[0]
print(f"   + Dòng nạp: Hồ sơ {line.dossier_id.name}, Loài {line.species_id.name}")

# Kích hoạt compute lượng tồn trên phần mềm của loài gỗ
line._compute_current_volume_species()
print(f"   + Tồn phần mềm tính toán của loài: {line.current_volume_species} m³")
assert line.current_volume_species == 100.0, "LỖI: Tồn phần mềm tính toán sai lệch!"

# 5. Nhập lượng thực tế mới (New Volume) là 95.5 m3, kiểm tra Onchange tính toán chênh lệch
line.write({'new_volume': 95.5})
line._onchange_new_volume()
print(f"-> Nhập khối lượng thực tế: {line.new_volume} m³")
print(f"   + Lượng chênh lệch tự động tính toán: {line.adjusted_volume} m³")

assert line.adjusted_volume == -4.5, "LỖI: Sai lệch lượng điều chỉnh tự động!"

# 6. Gửi phiếu rà soát
inventory.action_review()
print(f"-> Đã gửi rà soát phiếu kiểm kê. Trạng thái hiện tại: '{inventory.state}'")
assert inventory.state == 'review', "LỖI: Không chuyển được trạng thái sang Rà soát!"

# 7. Duyệt phiếu hoàn thành (Done)
inventory.action_done()
print(f"-> Đã Duyệt hoàn thành phiếu kiểm kê. Trạng thái hiện tại: '{inventory.state}'")
assert inventory.state == 'done', "LỖI: Không chuyển được trạng thái sang Hoàn thành!"

# 8. Xác nhận tồn kho của hồ sơ gỗ đã được cập nhật thành công xuống 95.5 m3
dossier._compute_stock_quantities()
print(f"-> Kiểm tra tồn kho của Hồ sơ gỗ sau khi duyệt:")
print(f"   + Tồn kho thực tế mới: {dossier.remaining_qty} m³")
print(f"   + Đã tiêu hao: {dossier.qty_consumed} m³")

assert dossier.remaining_qty == 95.5, "LỖI: Tồn kho của hồ sơ gỗ không được cập nhật sau khi hoàn thành!"
assert line.ledger_id, "LỖI: Không tự động tạo bản ghi Sổ cái (Ledger)!"
print(f"   + Bản ghi Sổ Cái liên kết: {line.ledger_id.id} [Khối lượng: {line.ledger_id.actual_qty} m³]")

# 9. Thực hiện Rollback (Hủy phiếu kiểm kê)
print("-> Bắt đầu kiểm thử cơ chế Rollback...")
inventory.action_cancel()
print(f"   + Trạng thái phiếu kiểm kê sau Rollback: '{inventory.state}'")
assert inventory.state == 'cancel', "LỖI: Không chuyển được trạng thái sang Hủy!"

# 10. Xác nhận bản ghi Sổ cái đã bị xóa sạch và tồn kho quay lại 100.0 m3
dossier._compute_stock_quantities()
print(f"-> Kiểm tra tồn kho của Hồ sơ gỗ sau Rollback:")
print(f"   + Tồn kho thực tế hoàn nguyên: {dossier.remaining_qty} m³")

assert dossier.remaining_qty == 100.0, "LỖI: Rollback thất bại! Tồn kho không quay lại lượng ban đầu."
assert not line.ledger_id, "LỖI: Bản ghi Sổ cái không được xóa khỏi dòng chi tiết!"

# Dọn dẹp dữ liệu kiểm thử tránh rác database
inventory.unlink()
dossier.unlink()
if 'species' in locals():
    species.unlink()
print("======================================================================")
print("CHÚC MỪNG! TẤT CẢ CÁC BƯỚC KIỂM THỬ ĐÃ THÀNH CÔNG VỚI KẾT QUẢ HOÀN HẢO!")
print("======================================================================")
env.cr.commit()
