import os
import sys

# Thêm đường dẫn project vào sys.path
sys.path.append('/Users/sonzai/dev/odoo 19/odoo')

import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

def run_test():
    # Khởi tạo cấu hình Odoo
    odoo.tools.config.parse_config(['-c', 'odoo.conf'])
    registry = Registry('odoo_db_production')

    print("======================================================================")
    print("BẮT ĐẦU CHẠY THỬ NGHIỆM KIỂM THỬ TỰ ĐỘNG - LUỒNG SẢN XUẤT GỖ")
    print("======================================================================")

    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # 1. Tìm kiếm dữ liệu đầu vào
        print("\n--- 1. TÌM KIẾM DỮ LIỆU ĐẦU VÀO ---")
        
        # Tìm công ty
        company = env['res.company'].search([], limit=1)
        if not company:
            print("LỖI: Không tìm thấy công ty nào!")
            return
        print(f"Sử dụng công ty: {company.name} [ID: {company.id}]")
        
        # Tìm hoặc tạo nhà cung cấp dùng chung cho mockup
        supplier = env['res.partner'].search([('name', '=', 'Nhà cung cấp Gỗ Test')], limit=1)
        if not supplier:
            supplier = env['res.partner'].create({
                'name': 'Nhà cung cấp Gỗ Test',
                'x_is_wood_customer': False,
            })
        
        # Tìm sản phẩm gỗ test (tìm theo tên chính xác để đảm bảo thuộc tính mockup)
        product = env['product.product'].search([
            ('name', '=', 'Gỗ thành phẩm Test M2O')
        ], limit=1)
        
        if not product:
            # Tạo sản phẩm gỗ mockup
            product = env['product.product'].create({
                'name': 'Gỗ thành phẩm Test M2O',
                'is_wood_product': True,
                'x_is_wood_product': True,
                'sale_ok': True,
                'list_price': 100000,
                'uom_id': env.ref('uom.product_uom_unit').id,
                'x_unit': 'sheet',
                'x_volume_m3': 0.05, # 0.05 m3 mỗi tấm
            })
            print(f"Đã tạo mockup sản phẩm gỗ thành phẩm: {product.name}")
        else:
            print(f"Sử dụng sản phẩm gỗ: {product.name} [ID: {product.id}, ĐVT: {product.uom_id.name}]")

        # Tìm hồ sơ gỗ nguồn (dl.wood.dossier) có trạng thái 'using' và còn tồn khả dụng > 0
        dossiers_avail = env['dl.wood.dossier'].search([
            ('company_id', '=', company.id),
            ('state', '=', 'using')
        ]).filtered(lambda d: any(line.x_qty_available > 0.01 for line in d.line_ids))
        
        if not dossiers_avail:
            print("Không tìm thấy hồ sơ gỗ nguồn ở trạng thái 'using' còn tồn. Tạo mockup...")
            # Tìm hoặc tạo loài gỗ
            species = env['dl.wood.species'].search([], limit=1)
            if not species:
                species = env['dl.wood.species'].create({'name': 'Keo Lai'})
            
            # Tìm hoặc tạo phân loại chất lượng gỗ
            grade = env['dl.wood.species.grade'].search([('species_id', '=', species.id)], limit=1)
            if not grade:
                grade = env['dl.wood.species.grade'].create({
                    'species_id': species.id,
                    'name': 'Loại A',
                    'height': 2.0,
                    'default_price': 2000000,
                })

            # Tạo hồ sơ gỗ nguồn ở dạng nháp (draft) trước
            dossier = env['dl.wood.dossier'].create({
                'name': 'HSG_TEST_M2O_01',
                'company_id': company.id,
                'partner_id': supplier.id,
                'state': 'draft',
            })
            # Tạo dòng chi tiết hồ sơ (Lưu ý: Bắt buộc truyền volume để có tồn khả dụng!)
            env['dl.wood.dossier.line'].create({
                'dossier_id': dossier.id,
                'species_id': species.id,
                'grade_id': grade.id,
                'height': 2.0,
                'quantity': 100,
                'volume': 50, # Gán volume = 50 m3 để có tồn khả dụng
                'price_unit': 2000000,
            })
            
            # Chuyển hồ sơ sang trạng thái using
            dossier.state = 'using'
            print(f"Đã tạo mockup hồ sơ gỗ nguồn và chuyển sang 'using': {dossier.name} có 1 dòng chi tiết loài {species.name}")
        else:
            dossier = dossiers_avail[0]
            print(f"Sử dụng hồ sơ gỗ nguồn có sẵn: {dossier.name} [ID: {dossier.id}]")

        # Tìm loài gỗ và dòng chi tiết đầu tiên của hồ sơ gỗ nguồn
        valid_lines = dossier.line_ids.filtered(lambda l: l.x_qty_available > 0.01)
        if valid_lines:
            first_dossier_line = valid_lines[0]
            first_species = first_dossier_line.species_id
            print(f"-> Loài gỗ đầu tiên có tồn trong hồ sơ: {first_species.name}")
            print(f"-> Dòng chi tiết gỗ đầu tiên: {first_dossier_line.grade_id.name if first_dossier_line.grade_id else 'Mặc định'} ({first_dossier_line.height}m) [Tồn KD: {first_dossier_line.x_qty_available} m³]")
        else:
            print("LỖI: Hồ sơ gỗ nguồn không có dòng chi tiết nào còn tồn khả dụng!")
            cr.rollback()
            return

        # Tìm hồ sơ ván bóc (dl.wood.peeling.dossier) có trạng thái 'using' và có hóa đơn còn tồn > 0
        peeling_dossiers_avail = env['dl.wood.peeling.dossier'].search([
            ('company_id', '=', company.id),
            ('state', '=', 'using')
        ]).filtered(lambda pd: any(inv.qty_available > 0.01 for inv in pd.invoice_ids))
        
        if not peeling_dossiers_avail:
            print("Không tìm thấy hồ sơ ván bóc ở trạng thái 'using' còn tồn. Tạo mockup...")
            # Tạo hồ sơ ván bóc ở dạng nháp
            peeling_dossier = env['dl.wood.peeling.dossier'].create({
                'name': 'HSV_TEST_M2O_01',
                'company_id': company.id,
                'partner_id': supplier.id,
                'state': 'draft',
            })
            # Tạo hóa đơn ván bóc
            env['dl.wood.peeling.invoice'].create({
                'dossier_id': peeling_dossier.id,
                'invoice_number': 'HD_V_01',
                'invoice_date': '2026-01-01',
                'qty_initial': 50.0,
                'qty_used': 0.0,
                'price_unit': 1800000,
                'state': 'available',
            })
            
            # Chuyển sang using
            peeling_dossier.state = 'using'
            print(f"Đã tạo mockup hồ sơ ván bóc và chuyển sang 'using': {peeling_dossier.name} có 1 hóa đơn HD_V_01 (Tồn 50 m³)")
        else:
            peeling_dossier = peeling_dossiers_avail[0]
            print(f"Sử dụng hồ sơ ván bóc có sẵn: {peeling_dossier.name} [ID: {peeling_dossier.id}]")

        # Tìm hóa đơn ván bóc đầu tiên còn tồn
        avail_invoices = peeling_dossier.invoice_ids.filtered(lambda inv: inv.qty_available > 0.01).sorted('invoice_date')
        if not avail_invoices:
            # Chuyển về draft để tạo invoice mới nếu cần
            peeling_dossier.state = 'draft'
            env['dl.wood.peeling.invoice'].create({
                'dossier_id': peeling_dossier.id,
                'invoice_number': 'HD_V_NEW_01',
                'invoice_date': '2026-05-26',
                'qty_initial': 30.0,
                'qty_used': 0.0,
                'price_unit': 1900000,
                'state': 'available',
            })
            peeling_dossier.state = 'using'
            avail_invoices = peeling_dossier.invoice_ids.filtered(lambda inv: inv.qty_available > 0.01).sorted('invoice_date')
        
        first_invoice = avail_invoices[0]
        print(f"-> Hóa đơn ván bóc đầu tiên còn tồn: {first_invoice.invoice_number} [Tồn KD: {first_invoice.qty_available} m³]")

        # 2. Tạo Lệnh sản xuất mới
        print("\n--- 2. TẠO LỆNH SẢN XUẤT NHÁP (DRAFT) ---")
        order = env['dl.wood.production.order'].create({
            'product_id': product.id,
            'qty_planned': 100.0, # 100 tấm => 100 * 0.05 = 5.0 m3 thành phẩm
            'date_planned': '2026-05-26',
            'x_co_yield_wood': 1.3,
            'x_co_yield_peeling': 1.1,
            'state': 'draft',
        })
        print(f"Lệnh sản xuất đã tạo: {order.name} [Trạng thái: {order.state}]")
        print(f"Khối lượng thành phẩm kế hoạch: {order.x_qty_planned_m3} m³")

        # 3. Tạo dòng tiêu hao gỗ và test tự động điền (Defaulting)
        print("\n--- 3. TEST TỰ ĐỘNG ĐIỀN CHO GỖ ---")
        line = env['dl.wood.production.line'].new({
            'production_order_id': order.id,
            'dossier_id': dossier.id,
        })
        
        # Trigger onchange dossier_id
        line._onchange_dossier_id()
        
        print("KẾT QUẢ TỰ ĐỘNG ĐIỀN KHI CHỌN HỒ SƠ GỖ:")
        print(f"- Loài gỗ được chọn: {line.species_id.name if line.species_id else 'None'} (Mong muốn: {first_species.name})")
        print(f"- Phân loại gỗ được chọn: {line.x_dossier_line_id.grade_id.name if line.x_dossier_line_id and line.x_dossier_line_id.grade_id else 'Mặc định'} ({line.x_dossier_line_id.height if line.x_dossier_line_id else 0}m) (Mong muốn: {first_dossier_line.grade_id.name if first_dossier_line.grade_id else 'Mặc định'})")
        
        assert line.species_id == first_species, "LỖI: Sai loài gỗ mặc định!"
        assert line.x_dossier_line_id == first_dossier_line, "LỖI: Sai dòng chi tiết gỗ mặc định!"
        print("=> Đạt yêu cầu: Tự động điền loài gỗ và phân loại gỗ đầu tiên thành công!")

        # Lưu dòng gỗ vào database trong transaction
        wood_line_vals = line._convert_to_write(line._cache)
        wood_line_vals['production_order_id'] = order.id
        wood_line = env['dl.wood.production.line'].create(wood_line_vals)
        print(f"Đã lưu dòng gỗ: Tồn KD: {wood_line.x_qty_available} m³, Định mức: {wood_line.x_ratio}%, KL KH: {wood_line.volume_planned} m³")

        # 4. Tạo dòng tiêu hao ván bóc và test tự động điền (Defaulting)
        print("\n--- 4. TEST TỰ ĐỘNG ĐIỀN CHO VÁN BÓC ---")
        p_line = env['dl.wood.peeling.production.line'].new({
            'production_order_id': order.id,
            'peeling_dossier_id': peeling_dossier.id,
        })
        
        # Trigger onchange peeling_dossier_id
        p_line._onchange_peeling_dossier_id()
        
        print("KẾT QUẢ TỰ ĐỘNG ĐIỀN KHI CHỌN HỒ SƠ VÁN BÓC:")
        print(f"- Hóa đơn được chọn: {p_line.peeling_invoice_id.invoice_number if p_line.peeling_invoice_id else 'None'} (Mong muốn: {first_invoice.invoice_number})")
        
        assert p_line.peeling_invoice_id == first_invoice, "LỖI: Sai hóa đơn ván bóc mặc định!"
        print("=> Đạt yêu cầu: Tự động điền hóa đơn ván bóc còn tồn đầu tiên thành công!")

        # Lưu dòng ván bóc vào database trong transaction
        peeling_line_vals = p_line._convert_to_write(p_line._cache)
        peeling_line_vals['production_order_id'] = order.id
        peeling_line = env['dl.wood.peeling.production.line'].create(peeling_line_vals)
        print(f"Đã lưu dòng ván bóc: Tồn KD: {peeling_line.x_qty_available} m³, Định mức: {peeling_line.x_ratio}%, KL KH: {peeling_line.volume_planned} m³")

        # Cập nhật định mức của 2 dòng cho đủ 100% (Ví dụ: Gỗ 60%, Ván bóc 40%)
        print("\n--- 5. THIẾT LẬP ĐỊNH MỨC VÀ KIỂM TRA TÍNH TOÁN KHỐI LƯỢNG KẾ HOẠCH ---")
        wood_line.write({'x_ratio': 60.0})
        wood_line._onchange_ratio_and_co()
        peeling_line.write({'x_ratio': 40.0})
        peeling_line._onchange_ratio_and_co()
        
        # Force compute các trường liên quan trên lệnh SX
        order._compute_total_volume()
        
        print(f"Tổng định mức: {order.x_total_ratio}%")
        print(f"KL kế hoạch gỗ: {wood_line.volume_planned} m³ (Công thức: 100 tấm * 0.05 m3/tấm * 1.3 CO * 60% = 3.9 m³)")
        print(f"KL kế hoạch ván bóc: {peeling_line.volume_planned} m³ (Công thức: 100 tấm * 0.05 m3/tấm * 1.1 CO * 40% = 2.2 m³)")
        
        assert abs(wood_line.volume_planned - 3.9) < 0.05, "LỖI: Sai khối lượng kế hoạch gỗ!"
        assert abs(peeling_line.volume_planned - 2.2) < 0.05, "LỖI: Sai khối lượng kế hoạch ván bóc!"
        print("=> Đạt yêu cầu: Tính toán khối lượng kế hoạch chính xác!")

        # 6. Bắt đầu sản xuất (action_start)
        print("\n--- 6. BẮT ĐẦU SẢN XUẤT (action_start) ---")
        order.action_start()
        print(f"Trạng thái lệnh: {order.state} (Mong muốn: in_progress)")
        assert order.state == 'in_progress', "LỖI: Trạng thái không chuyển sang in_progress!"
        print("=> Đạt yêu cầu: Bắt đầu sản xuất thành công!")

        # 7. Hoàn thành sản xuất (action_done)
        print("\n--- 7. HOÀN THÀNH SẢN XUẤT (action_done) ---")
        # Giả sử thực tế sản xuất hoàn thành đúng kế hoạch
        wood_line.write({'volume_actual': 3.9})
        peeling_line.write({'volume_actual': 2.2})
        
        # Lưu tồn kho khả dụng trước khi hoàn thành để so sánh
        wood_avail_before = wood_line.x_qty_available
        peeling_avail_before = peeling_line.x_qty_available
        peeling_invoice_used_before = first_invoice.qty_used
        
        order.action_done()
        print(f"Trạng thái lệnh: {order.state} (Mong muốn: done)")
        assert order.state == 'done', "LỖI: Trạng thái không chuyển sang done!"
        
        # Kiểm tra trừ lùi tồn kho
        # Đối với gỗ: Kiểm tra xem có bản ghi Ledger âm được tạo ra không
        ledgers = env['dl.dossier.ledger'].search([('production_id', '=', order.id)])
        print(f"Số lượng bản ghi sổ cái gỗ được tạo: {len(ledgers)}")
        assert len(ledgers) > 0, "LỖI: Không tạo bản ghi sổ cái gỗ!"
        total_deducted_wood = -sum(ledgers.mapped('actual_qty'))
        print(f"Tổng khối lượng gỗ đã trừ trong sổ cái: {total_deducted_wood} m³ (Mong muốn: 3.9 m³)")
        assert abs(total_deducted_wood - 3.9) < 0.01, "LỖI: Sai khối lượng gỗ trừ lùi!"
        
        # Đối với ván bóc: Kiểm tra xem trường qty_used của hóa đơn ván bóc có tăng lên không
        peeling_deducted = first_invoice.qty_used - peeling_invoice_used_before
        print(f"Khối lượng ván bóc đã dùng thêm trên hóa đơn: {peeling_deducted} m³ (Mong muốn: 2.2 m³)")
        assert abs(peeling_deducted - 2.2) < 0.01, "LỖI: Sai khối lượng ván bóc trừ lùi!"
        print("=> Đạt yêu cầu: Khấu trừ tồn kho thực tế gỗ và ván bóc chính xác!")

        # 8. Quay lại trạng thái trước (action_previous_state: done -> in_progress)
        print("\n--- 8. QUAY LẠI TRẠNG THÁI TRƯỚC (action_previous_state: done -> in_progress) ---")
        order.action_previous_state()
        print(f"Trạng thái lệnh sau khi rollback: {order.state} (Mong muốn: in_progress)")
        assert order.state == 'in_progress', "LỖI: Trạng thái không quay về in_progress!"
        
        # Kiểm tra hoàn trả tồn kho
        # Đối với gỗ: Kiểm tra xem bản ghi Ledger có bị xóa không
        ledgers_after = env['dl.dossier.ledger'].search([('production_id', '=', order.id)])
        print(f"Số lượng bản ghi sổ cái gỗ sau rollback: {len(ledgers_after)} (Mong muốn: 0)")
        assert len(ledgers_after) == 0, "LỖI: Bản ghi sổ cái gỗ không bị xóa!"
        
        # Đối với ván bóc: Kiểm tra xem qty_used trên hóa đơn ván bóc có quay lại giá trị cũ không
        peeling_invoice_used_after = first_invoice.qty_used
        print(f"Khối lượng ván bóc đã dùng sau rollback: {peeling_invoice_used_after} m³ (Mong muốn: {peeling_invoice_used_before} m³)")
        assert abs(peeling_invoice_used_after - peeling_invoice_used_before) < 0.01, "LỖI: Tồn kho ván bóc không được hoàn trả đúng!"
        print("=> Đạt yêu cầu: Hoàn trả tồn kho khi quay lại trạng thái trước thành công!")

        # Rollback toàn bộ transaction để tránh ghi đè dữ liệu thật vào DB
        cr.rollback()
        print("\n======================================================================")
        print("TẤT CẢ KIỂM THỬ ĐÃ THÀNH CÔNG RỰC RỠ! TRANSACTION ĐÃ ĐƯỢC ROLLBACK AN TOÀN.")
        print("======================================================================")

if __name__ == '__main__':
    run_test()
