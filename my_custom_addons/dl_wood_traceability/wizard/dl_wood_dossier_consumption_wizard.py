# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import io
import base64
from datetime import datetime, date

class DlWoodDossierConsumptionWizard(models.TransientModel):
    _name = 'dl.wood.dossier.consumption.wizard'
    _description = 'Wizard Xuất Báo Cáo Tiêu Hao Hồ Sơ Gỗ'

    dossier_ids = fields.Many2many(
        'dl.wood.dossier',
        string='Bộ hồ sơ gỗ',
        help='Chọn các bộ hồ sơ cần xuất báo cáo. Để trống để xuất toàn bộ.'
    )
    date_from = fields.Date(
        string='Từ ngày',
        help='Lọc theo ngày lập Lệnh sản xuất'
    )
    date_to = fields.Date(
        string='Đến ngày',
        help='Lọc theo ngày lập Lệnh sản xuất'
    )
    production_state = fields.Selection([
        ('all', 'Tất cả trạng thái'),
        ('draft', 'Dự thảo'),
        ('in_progress', 'Đang sản xuất'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái Lệnh sản xuất', default='all', required=True)

    file_data = fields.Binary(string='Tải xuống Báo cáo', readonly=True)
    file_name = fields.Char(string='Tên File', readonly=True)

    def action_export_excel(self):
        self.ensure_one()
        try:
            import xlsxwriter
        except ImportError:
            raise UserError(_("Thư viện xlsxwriter chưa được cài đặt. Vui lòng liên hệ Admin (pip install xlsxwriter)."))

        # 1. Xác định danh sách Hồ sơ gỗ cần xuất
        dossier_domain = [
            ('state', '!=', 'cancelled'),
            ('company_id', 'in', self.env.companies.ids)
        ]
        if self.dossier_ids:
            dossier_domain.append(('id', 'in', self.dossier_ids.ids))
        
        dossiers = self.env['dl.wood.dossier'].sudo().search(dossier_domain, order='id desc')
        if not dossiers:
            raise UserError(_("Không tìm thấy bộ hồ sơ gỗ nào phù hợp với bộ lọc."))

        # 2. Xác định danh sách dòng tiêu hao lệnh sản xuất liên quan
        line_domain = [
            ('dossier_id', 'in', dossiers.ids),
            ('company_id', 'in', self.env.companies.ids)
        ]
        if self.date_from:
            line_domain.append(('production_order_id.date_planned', '>=', self.date_from))
        if self.date_to:
            line_domain.append(('production_order_id.date_planned', '<=', self.date_to))
        if self.production_state != 'all':
            line_domain.append(('production_order_id.state', '=', self.production_state))

        prod_lines = self.env['dl.wood.production.line'].sudo().search(line_domain, order='dossier_id desc, production_order_id desc')

        # 3. Khởi tạo Workbook trong bộ nhớ
        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})

        # --- Các định dạng hiển thị (Formats) ---
        f_title = workbook.add_format({
            'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter', 'font_name': 'Arial'
        })
        f_subtitle = workbook.add_format({
            'font_size': 11, 'italic': True, 'align': 'center', 'valign': 'vcenter', 'font_name': 'Arial'
        })
        f_header = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#1f4e78', 'font_color': '#ffffff',
            'border': 1, 'text_wrap': True, 'font_name': 'Arial', 'font_size': 10
        })
        f_cell_center = workbook.add_format({
            'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_name': 'Arial', 'font_size': 9
        })
        f_cell_left = workbook.add_format({
            'align': 'left', 'valign': 'vcenter', 'border': 1, 'font_name': 'Arial', 'font_size': 9
        })
        
        # Định dạng số thực 2 chữ số thập phân
        f_cell_float = workbook.add_format({
            'num_format': '#,##0.00', 'align': 'right', 'valign': 'vcenter', 'border': 1, 'font_name': 'Arial', 'font_size': 9
        })
        f_cell_bold_float = workbook.add_format({
            'bold': True, 'num_format': '#,##0.00', 'align': 'right', 'valign': 'vcenter', 'border': 1, 'font_name': 'Arial', 'font_size': 10, 'bg_color': '#f2f2f2'
        })
        f_cell_bold_label = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_name': 'Arial', 'font_size': 10, 'bg_color': '#f2f2f2'
        })

        # Trạng thái hồ sơ map sang tiếng Việt
        dossier_state_map = {
            'draft': 'Nháp',
            'exploiting': 'Đang khai thác',
            'summary': 'Tổng hợp',
            'confirmed': 'Xác nhận',
            'cancelled': 'Đã hủy'
        }

        # Trạng thái Lệnh sản xuất map sang tiếng Việt
        prod_state_map = {
            'draft': 'Dự thảo',
            'in_progress': 'Đang sản xuất',
            'done': 'Hoàn thành',
            'cancelled': 'Đã hủy'
        }

        # =========================================================================
        # SHEET 1: TỔNG HỢP HỒ SƠ GỖ
        # =========================================================================
        sheet1 = workbook.add_worksheet('Tổng Hợp Hồ Sơ Gỗ')
        sheet1.freeze_panes(4, 2)  # Cố định STT và Mã Hồ Sơ

        # Độ rộng các cột
        sheet1.set_column(0, 0, 6)   # STT
        sheet1.set_column(1, 1, 16)  # Mã Hồ Sơ
        sheet1.set_column(2, 2, 25)  # Tên Hồ Sơ
        sheet1.set_column(3, 3, 30)  # Chủ Rừng / Nhà Cung Cấp
        sheet1.set_column(4, 4, 25)  # Địa Bàn Khai Thác
        sheet1.set_column(5, 5, 12)  # Ngày Nhận
        sheet1.set_column(6, 10, 16) # Các cột số lượng m³
        sheet1.set_column(11, 11, 18) # Trạng thái

        # Viết tiêu đề
        sheet1.merge_range(0, 0, 0, 11, 'BÁO CÁO TỔNG HỢP HỒ SƠ GỖ HỆ THỐNG', f_title)
        
        filter_text = f"Bộ lọc: Toàn bộ hồ sơ gỗ hoạt động"
        if self.dossier_ids:
            filter_text = f"Bộ lọc: Lọc theo {len(self.dossier_ids)} hồ sơ được chọn"
        sheet1.merge_range(1, 0, 1, 11, filter_text, f_subtitle)

        # Viết tiêu đề cột
        headers1 = [
            'STT', 'Mã Hồ Sơ', 'Tên Hồ Sơ', 'Chủ Rừng / Nhà CC', 'Địa Bàn Khai Thác', 'Ngày Nhận',
            'Khối Lượng Bầu Đầu (m³)', 'Lượng Đã Dùng (m³)', 'Tồn Kho Thực Tế (m³)', 'Đang Giữ Đơn (m³)', 'Khả Dụng Bán (m³)', 'Trạng Thái'
        ]
        sheet1.set_row(3, 28)
        for i, h in enumerate(headers1):
            sheet1.write(3, i, h, f_header)

        # Đổ dữ liệu
        row = 4
        stt = 1
        for d in dossiers:
            sheet1.write(row, 0, stt, f_cell_center)
            sheet1.write(row, 1, d.name or '', f_cell_center)
            sheet1.write(row, 2, d.x_dossier_name or '', f_cell_left)
            sheet1.write(row, 3, d.partner_id.name or '', f_cell_left)
            sheet1.write(row, 4, d.exploitation_location_id.name or '', f_cell_left)
            sheet1.write(row, 5, d.date_received.strftime('%d/%m/%Y') if d.date_received else '', f_cell_center)
            
            sheet1.write_number(row, 6, d.initial_qty or 0.0, f_cell_float)
            sheet1.write_number(row, 7, d.qty_consumed or 0.0, f_cell_float)
            sheet1.write_number(row, 8, d.remaining_qty or 0.0, f_cell_float)
            sheet1.write_number(row, 9, d.qty_reserved or 0.0, f_cell_float)
            sheet1.write_number(row, 10, d.qty_available or 0.0, f_cell_float)
            sheet1.write(row, 11, dossier_state_map.get(d.state, d.state or ''), f_cell_center)
            
            row += 1
            stt += 1

        # Dòng tổng kết
        sheet1.write(row, 0, '', f_cell_bold_label)
        sheet1.merge_range(row, 1, row, 5, 'TỔNG CỘNG HỆ THỐNG', f_cell_bold_label)
        for c in range(6, 11):
            col_letter = chr(65 + c)
            if row > 4:
                sheet1.write_formula(row, c, f"=SUM({col_letter}5:{col_letter}{row})", f_cell_bold_float)
            else:
                sheet1.write_number(row, c, 0.0, f_cell_bold_float)
        sheet1.write(row, 11, '', f_cell_bold_label)


        # =========================================================================
        # SHEET 2: CHI TIẾT TIÊU HAO LỆNH SẢN XUẤT & KHAI CO
        # =========================================================================
        sheet2 = workbook.add_worksheet('Chi Tiết Tiêu Hao - Khai CO')
        sheet2.freeze_panes(4, 2)  # Cố định STT và Mã Hồ Sơ

        # Độ rộng các cột
        sheet2.set_column(0, 0, 6)   # STT
        sheet2.set_column(1, 1, 16)  # Mã Hồ Sơ
        sheet2.set_column(2, 2, 20)  # Đơn đặt hàng
        sheet2.set_column(3, 3, 22)  # Lệnh sản xuất
        sheet2.set_column(4, 4, 14)  # Trạng thái LSX
        sheet2.set_column(5, 5, 12)  # Ngày sản xuất
        sheet2.set_column(6, 6, 30)  # Thành phẩm sản xuất
        sheet2.set_column(7, 7, 15)  # Số lượng sản xuất
        sheet2.set_column(8, 8, 18)  # Loài gỗ tiêu hao
        sheet2.set_column(9, 9, 16)  # Định mức planned (m³)
        sheet2.set_column(10, 10, 16)  # Thực tế actual (m³)
        sheet2.set_column(11, 11, 14) # Hệ số Khai CO
        sheet2.set_column(12, 12, 14) # Tỷ lệ % định mức

        # Viết tiêu đề
        sheet2.merge_range(0, 0, 0, 12, 'CHI TIẾT TIÊU HAO NGUYÊN LIỆU TRONG LỆNH SẢN XUẤT', f_title)
        
        detail_filter_text = []
        if self.date_from:
            detail_filter_text.append(f"Từ {self.date_from.strftime('%d/%m/%Y')}")
        if self.date_to:
            detail_filter_text.append(f"Đến {self.date_to.strftime('%d/%m/%Y')}")
        if self.production_state != 'all':
            detail_filter_text.append(f"Trạng thái LSX: {prod_state_map.get(self.production_state)}")
        
        filter_str = f"Thời gian lọc: {', '.join(detail_filter_text) if detail_filter_text else 'Tất cả thời gian'}"
        sheet2.merge_range(1, 0, 1, 12, filter_str, f_subtitle)

        # Viết tiêu đề cột
        headers2 = [
            'STT', 'Mã Hồ Sơ', 'Đơn Đặt Hàng', 'Lệnh Sản Xuất', 'Trạng Thái LSX', 'Ngày Lập', 'Thành Phẩm Sản Xuất',
            'Số Lượng (Tấm)', 'Loài Gỗ Tiêu Hao', 'Định Mức Kế Hoạch (m³)', 'Thực Tế Tiêu Hao (m³)', 'Hệ Số Khai CO', 'Tỷ Lệ Định Mức (%)'
        ]
        sheet2.set_row(3, 28)
        for i, h in enumerate(headers2):
            sheet2.write(3, i, h, f_header)

        # Đổ dữ liệu
        row_detail = 4
        stt_detail = 1
        for line in prod_lines:
            order = line.production_order_id
            sheet2.write(row_detail, 0, stt_detail, f_cell_center)
            sheet2.write(row_detail, 1, line.dossier_id.name or '', f_cell_center)
            sheet2.write(row_detail, 2, order.sale_order_id.name or '', f_cell_center)
            sheet2.write(row_detail, 3, order.name or '', f_cell_center)
            sheet2.write(row_detail, 4, prod_state_map.get(order.state, order.state or ''), f_cell_center)
            sheet2.write(row_detail, 5, order.date_planned.strftime('%d/%m/%Y') if order.date_planned else '', f_cell_center)
            sheet2.write(row_detail, 6, order.product_id.name or '', f_cell_left)
            
            # Chọn số lượng kế hoạch hoặc thực tế tùy trạng thái
            qty = order.qty_planned if order.state == 'draft' else order.qty_done
            sheet2.write_number(row_detail, 7, qty or 0.0, f_cell_float)
            sheet2.write(row_detail, 8, line.species_id.name or '', f_cell_left)
            
            sheet2.write_number(row_detail, 9, line.volume_planned or 0.0, f_cell_float)
            sheet2.write_number(row_detail, 10, line.volume_actual or 0.0, f_cell_float)
            sheet2.write_number(row_detail, 11, line.x_co_yield or 0.0, f_cell_float)
            sheet2.write_number(row_detail, 12, line.x_ratio or 0.0, f_cell_float)
            
            row_detail += 1
            stt_detail += 1

        # Dòng tổng kết sheet chi tiết
        sheet2.write(row_detail, 0, '', f_cell_bold_label)
        sheet2.merge_range(row_detail, 1, row_detail, 8, 'TỔNG CỘNG TIÊU HAO', f_cell_bold_label)
        if row_detail > 4:
            sheet2.write_formula(row_detail, 9, f"=SUM(J5:J{row_detail})", f_cell_bold_float)
            sheet2.write_formula(row_detail, 10, f"=SUM(K5:K{row_detail})", f_cell_bold_float)
        else:
            sheet2.write_number(row_detail, 9, 0.0, f_cell_bold_float)
            sheet2.write_number(row_detail, 10, 0.0, f_cell_bold_float)
        sheet2.write(row_detail, 11, '', f_cell_bold_label)
        sheet2.write(row_detail, 12, '', f_cell_bold_label)

        workbook.close()
        
        # 4. Lưu dữ liệu Base64
        excel_data = base64.b64encode(buffer.getvalue())
        self.write({
            'file_data': excel_data,
            'file_name': f'Bao_Cao_Tieu_Hao_Ho_So_Go_{fields.Date.today().strftime("%Y%m%d")}.xlsx'
        })

        # Mở lại wizard để người dùng bấm nút tải xuống file
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dl.wood.dossier.consumption.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
