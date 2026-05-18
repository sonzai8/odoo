# -*- coding: utf-8 -*-
import os
import sys

# Thêm đường dẫn Odoo vào python path
sys.path.append('/Users/sonzai/dev/odoo 19/odoo')

import odoo
import odoo
from odoo import api, tools

tools.config.parse_config(['-c', 'odoo.conf'])

def test_previous_state():
    # Khởi tạo registry Odoo
    reg = odoo.modules.registry.Registry('odoo_db')
    with reg.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        # 1. Tìm hoặc tạo loài gỗ và hồ sơ gỗ mẫu để test
        species = env['dl.wood.species'].search([], limit=1)
        if not species:
            species = env['dl.wood.species'].create({
                'name': 'Gỗ Keo Test State',
            })
            
        dossier = env['dl.wood.dossier'].search([('remaining_qty', '>', 50)], limit=1)
        if not dossier:
            dossier = env['dl.wood.dossier'].create({
                'name': 'HS-TEST-STATE',
                'forest_owner_id': env['res.partner'].search([], limit=1).id or False,
                'initial_qty': 100.0,
                'remaining_qty': 100.0,
            })
            
        initial_remaining_qty = dossier.remaining_qty
        print(f"Hồ sơ gỗ ban đầu: {dossier.name} - Tồn kho: {initial_remaining_qty} m3")
        
        # 2. Tạo Lệnh sản xuất mẫu ở dạng Dự thảo (draft)
        product = env['product.product'].search([], limit=1)
        order = env['dl.wood.production.order'].create({
            'name': 'LSX-TEST-REVERT',
            'product_id': product.id if product else False,
            'qty_planned': 10.0,
            'qty_done': 10.0,
            'x_co_yield': 1.3,
            'state': 'draft',
        })
        print(f"1. Đã tạo Lệnh sản xuất: {order.name} - Trạng thái: {order.state}")
        
        # 3. Tạo dòng tiêu hao NVL
        line = env['dl.wood.production.line'].create({
            'production_order_id': order.id,
            'dossier_id': dossier.id,
            'species_id': species.id,
            'x_ratio': 100.0,
            'x_co_yield': 1.3,
            'volume_planned': 13.0,
            'volume_actual': 13.0,
        })
        print(f"Đã tạo dòng tiêu hao NVL với KL thực tế: {line.volume_actual} m3")
        
        # 4. Bắt đầu sản xuất (in_progress)
        order.action_start()
        print(f"2. Chuyển sang sản xuất - Trạng thái: {order.state}")
        
        # 5. Thử quay về Draft từ in_progress
        order.action_previous_state()
        print(f"3. Quay lại trạng thái trước từ 'in_progress' - Trạng thái: {order.state}")
        assert order.state == 'draft', "Quay về draft thất bại!"
        
        # 6. Chuyển lại sang in_progress để chuẩn bị hoàn thành
        order.action_start()
        print(f"4. Chuyển lại sang sản xuất - Trạng thái: {order.state}")
        
        # 7. Hoàn thành lệnh sản xuất (done)
        order.action_done()
        cr.commit() # Lưu vào DB tạm thời
        print(f"5. Đã bấm Hoàn thành - Trạng thái: {order.state}")
        print(f"Tồn kho hồ sơ sau khi Hoàn thành: {dossier.remaining_qty} m3 (mong đợi: {initial_remaining_qty - 13.0})")
        assert dossier.remaining_qty == initial_remaining_qty - 13.0, "Trừ kho sai lệch!"
        
        # Kiểm tra Ledger
        ledgers = env['dl.dossier.ledger'].search([('production_id', '=', order.id)])
        print(f"Số lượng bản ghi Ledger được tạo: {len(ledgers)}")
        assert len(ledgers) == 1, "Ledger không được tạo đúng!"
        assert ledgers.actual_qty == -13.0, "Lượng biến động Ledger sai lệch!"
        
        # 8. Bấm Quay lại trạng thái trước từ Done -> in_progress
        order.action_previous_state()
        cr.commit()
        print(f"6. Đã bấm Quay lại trạng thái trước từ 'done' - Trạng thái: {order.state}")
        print(f"Tồn kho hồ sơ sau khi phục hồi: {dossier.remaining_qty} m3 (mong đợi: {initial_remaining_qty})")
        assert order.state == 'in_progress', "Không quay về in_progress!"
        assert dossier.remaining_qty == initial_remaining_qty, "Phục hồi kho thất bại!"
        
        # Kiểm tra Ledger đã bị xóa chưa
        ledgers_after = env['dl.dossier.ledger'].search([('production_id', '=', order.id)])
        print(f"Số lượng bản ghi Ledger sau khi phục hồi: {len(ledgers_after)}")
        assert len(ledgers_after) == 0, "Ledger chưa bị xóa!"
        
        # Dọn dẹp dữ liệu test
        order.action_draft()
        order.unlink()
        print("=== KIỂM THỬ THÀNH CÔNG 100% ===")

if __name__ == '__main__':
    test_previous_state()
