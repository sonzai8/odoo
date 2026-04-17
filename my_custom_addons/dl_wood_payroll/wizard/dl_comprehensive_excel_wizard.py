from odoo import models, fields, api, _
from odoo.exceptions import UserError
import io
import base64
import calendar
from datetime import datetime, date

class ComprehensiveExcelWizard(models.TransientModel):
    _name = 'dl.comprehensive.excel.wizard'
    _description = 'Wizard Xuất Excel Tổng Hợp'

    month = fields.Selection([(str(i), str(i)) for i in range(1, 13)], string='Tháng', default=str(fields.Date.today().month), required=True)
    year = fields.Integer(string='Năm', default=fields.Date.today().year, required=True)
    
    file_data = fields.Binary('File Excel', readonly=True)
    file_name = fields.Char('Tên File', readonly=True)

    force_export = fields.Boolean(default=False)
    draft_log_count = fields.Integer(compute='_compute_drafts')

    @api.depends('month', 'year')
    def _compute_drafts(self):
        for rec in self:
            if rec.month and rec.year:
                start_date = date(rec.year, int(rec.month), 1)
                _, last_day = calendar.monthrange(rec.year, int(rec.month))
                end_date = date(rec.year, int(rec.month), last_day)

                rec.draft_log_count = self.env['dl.production.log'].search_count([
                    ('date', '>=', start_date),
                    ('date', '<=', end_date),
                    ('state', '=', 'draft')
                ])
            else:
                rec.draft_log_count = 0

    def action_view_draft_logs(self):
        self.ensure_one()
        start_date = date(self.year, int(self.month), 1)
        _, last_day = calendar.monthrange(self.year, int(self.month))
        end_date = date(self.year, int(self.month), last_day)

        drafts = self.env['dl.production.log'].search([
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('state', '=', 'draft')
        ])
        return {
            'name': 'Sản lượng chưa duyệt',
            'type': 'ir.actions.act_window',
            'res_model': 'dl.production.log',
            'view_mode': 'list,form',
            'domain': [('id', 'in', drafts.ids)],
            'target': 'current',
        }

    def action_force_export(self):
        self.ensure_one()
        self.force_export = True
        return self.action_export()

    def action_export(self):
        if not self.force_export and self.draft_log_count > 0:
            return {
                'name': 'Cảnh báo: Có dữ liệu nháp (Chưa duyệt)!',
                'type': 'ir.actions.act_window',
                'res_model': 'dl.comprehensive.excel.wizard',
                'view_mode': 'form',
                'res_id': self.id,
                'view_id': self.env.ref('dl_wood_payroll.view_dl_comprehensive_excel_wizard_warning_form').id,
                'target': 'new',
            }
        try:
            import xlsxwriter
            from xlsxwriter.utility import xl_col_to_name
        except ImportError:
            raise UserError(_("Thư viện xlsxwriter chưa được cài đặt. Vui lòng liên hệ Admin (pip install xlsxwriter)."))

        start_date = date(self.year, int(self.month), 1)
        _, last_day = calendar.monthrange(self.year, int(self.month))
        end_date = date(self.year, int(self.month), last_day)

        groups = self.env['dl.production.group'].search([])
        if not groups:
            raise UserError("Không có tổ sản xuất nào trong hệ thống.")

        pricelist = self.env['dl.piece.rate.pricelist'].search([
            ('month', '=', int(self.month)),
            ('year', '=', self.year),
            ('state', '=', 'confirmed')
        ], limit=1)
        
        req_days = pricelist.x_required_days if pricelist else 0

        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
        
        # --- Formats ---
        f_title = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter'})
        f_header = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#f2dede', 'border': 1, 'text_wrap': True})
        f_header_emp = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#ffeb3b', 'border': 1})
        f_header_pro = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#d9edf7', 'border': 1})
        f_cell_center = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
        money_fmt = '#,##0 "₫"'
        f_cell_money = workbook.add_format({'num_format': money_fmt, 'align': 'right', 'valign': 'vcenter', 'border': 1})
        f_cell_formula = workbook.add_format({'num_format': money_fmt, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color': '#e8f5e9'})
        f_cell_bold_money = workbook.add_format({'bold': True, 'num_format': money_fmt, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color': '#eef1f5'})
        # Càc format màu đặc biệt cho bảng chấm công
        f_cell_absent = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#FFFF00'})    # Vàng - nghỉ
        f_cell_partial = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#FFFACD'})   # Vàng nhạt - công < 1
        f_cell_lent_out = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#FF8C00'}) # Cam đậm - cho mượn
        f_cell_note = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'border': 1, 'text_wrap': True, 'font_size': 8})
        
        # Format con cho lương (màu + tiền)
        f_salary_absent = workbook.add_format({'num_format': money_fmt, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color': '#FFFF00'})
        f_salary_partial = workbook.add_format({'num_format': money_fmt, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color': '#FFFACD'})
        f_salary_lent_out = workbook.add_format({'num_format': money_fmt, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color': '#FF8C00'})
        
        sheets_created = 0

        # Map Excel Locations ahead of time for cross-sheet references
        group_maps = {}
        group_data_cache = {}
        
        for group in groups:
            logs = self.env['dl.production.log'].search([
                ('production_group_id', '=', group.id),
                ('date', '>=', start_date),
                ('date', '<=', end_date),
                ('state', 'in', ['confirmed', 'locked'])
            ])
            pool_results = self.env['dl.daily.pooling.result'].search([
                ('source_group_id', '=', group.id),
                ('date', '>=', start_date),
                ('date', '<=', end_date),
            ])
            if not logs and not pool_results:
                continue
                
            products = set()
            for log in logs:
                for pl in log.product_line_ids:
                    products.add(pl.product_id)
            products = list(products)
            products.sort(key=lambda p: p.name)
            M = len(products)
            
            sheet_name = "".join([c for c in f"Tổ {group.name}" if c.isalnum() or c in (' ', '_')])[:31]
            employee_ids = set([r.employee_id.id for r in pool_results])
            native_emps = self.env['hr.employee'].search([('x_source_group_id', '=', group.id)])
            employee_ids.update(native_emps.ids)
            employees = self.env['hr.employee'].browse(list(employee_ids)).sorted(key=lambda e: e.name)
            
            group_maps[group.id] = {
                'sheet_name': f"'{sheet_name}'",
                'M': M,
                'c_sc_ngoai': xl_col_to_name(M + 1),
                'c_tra_cao': xl_col_to_name(M + 2),
                'c_tra_thap': xl_col_to_name(M + 3),
            }
            
            group_data_cache[group.id] = {
                'logs': logs,
                'pool_results': pool_results,
                'products': products,
                'employees': employees,
                'sheet_name': sheet_name
            }

        for group_id, cache in group_data_cache.items():
            group = self.env['dl.production.group'].browse(group_id)
            sheets_created += 1
            sheet = workbook.add_worksheet(cache['sheet_name'])
            
            logs = cache['logs']
            pool_results = cache['pool_results']
            products = cache['products']
            employees = cache['employees']
            M = len(products)
            E = len(employees)
            
            idx_sc_sx = M + 1   # Tổng SC Sản Xuất (Tham gia làm ra SP hôm nay)
            idx_sc_ngoai = M + 2
            idx_tra_cao = M + 3
            idx_tra_thap = M + 4
            idx_tu_ngoai_cao = M + 5
            idx_tu_ngoai_thap = M + 6
            idx_dt_cao = M + 7
            idx_dt_thap = M + 8
            idx_sc_noi_bo = M + 9
            idx_avg_cao = M + 10
            idx_avg_thap = M + 11
            
            idx_salary_start = M + 12
            
            # Freeze Panes (Chỉ cột ngày)
            sheet.freeze_panes(5, 1)

            # Columns Size for Top Grid
            sheet.set_column(0, 0, 8)  
            for i in range(M):
                sheet.set_column(i+1, i+1, 10) 
            sheet.set_column(idx_sc_sx, idx_sc_sx, 12)
            sheet.set_column(idx_sc_ngoai, idx_tu_ngoai_thap, 13)
            sheet.set_column(idx_dt_cao, idx_dt_thap, 15) 
            sheet.set_column(idx_sc_noi_bo, idx_sc_noi_bo, 8) 
            if E > 0:
                idx_top_note_col = idx_salary_start + E
            else:
                idx_top_note_col = idx_salary_start

            # Đương kẻ max_col_top bao gồm cả cột ghi chú
            max_col_top = idx_top_note_col
            sheet.merge_range(0, 0, 0, max_col_top, f"BÁO CÁO MATRIX LƯƠNG & SẢN LƯỢNG - TỔ {group.name.upper()} - {self.month}/{self.year}", f_title)

            sheet.merge_range(1, 0, 4, 0, "Ngày", f_header)
            sheet.write(3, 0, "ĐG CAO", f_header_pro)
            sheet.write(4, 0, "ĐG THẤP", f_header_pro)

            if M > 0:
                sheet.merge_range(1, 1, 1, M, "SẢN LƯỢNG MẶT HÀNG", f_header_pro)
                for i, p in enumerate(products):
                    sheet.write(2, i + 1, p.name[:30] if p.name else '', f_header_pro)
                    price_line = False
                    if pricelist:
                        price_line = pricelist.line_ids.filtered(lambda l: l.product_id.id == p.id and l.department_id.id == group.department_id.id)
                    sheet.write_number(3, i + 1, price_line[0].price_high if price_line else 0, f_cell_money)
                    sheet.write_number(4, i + 1, price_line[0].price_low if price_line else 0, f_cell_money)
            else:
                sheet.write(1, 1, "SẢN LƯỢNG MẶT HÀNG", f_header_pro)

            sheet.merge_range(1, idx_sc_sx, 4, idx_sc_sx, "Tổng SC\nSản Xuất", f_header)
            sheet.merge_range(1, idx_sc_ngoai, 4, idx_sc_ngoai, "SC Khách\nĐến Làm", f_header)
            
            sheet.merge_range(1, idx_tra_cao, 2, idx_tra_thap, "Tiền Phải Trả Cho Tổ Khác", f_header)
            sheet.write(3, idx_tra_cao, "(Cao)", f_header_pro)
            sheet.write(4, idx_tra_cao, "", f_header_pro)
            sheet.write(3, idx_tra_thap, "(Thấp)", f_header_pro)
            sheet.write(4, idx_tra_thap, "", f_header_pro)
            
            sheet.merge_range(1, idx_tu_ngoai_cao, 2, idx_tu_ngoai_thap, "Tiền Nhận Từ Tổ Khác", f_header)
            sheet.write(3, idx_tu_ngoai_cao, "(Cao)", f_header_pro)
            sheet.write(4, idx_tu_ngoai_cao, "", f_header_pro)
            sheet.write(3, idx_tu_ngoai_thap, "(Thấp)", f_header_pro)
            sheet.write(4, idx_tu_ngoai_thap, "", f_header_pro)
            
            sheet.merge_range(1, idx_dt_cao, 2, idx_dt_thap, "Doanh Thu Ròng", f_header)
            sheet.write(3, idx_dt_cao, "(Cao)", f_header_pro)
            sheet.write(4, idx_dt_cao, "", f_header_pro)
            sheet.write(3, idx_dt_thap, "(Thấp)", f_header_pro)
            sheet.write(4, idx_dt_thap, "", f_header_pro)
            
            sheet.merge_range(1, idx_sc_noi_bo, 4, idx_sc_noi_bo, "Tổng SC\nChấm Công", f_header)
            
            sheet.merge_range(1, idx_avg_cao, 4, idx_avg_cao, "Thu nhập TB\n(Cao)", f_header)
            sheet.merge_range(1, idx_avg_thap, 4, idx_avg_thap, "Thu nhập TB\n(Thấp)", f_header)
            sheet.set_column(idx_avg_cao, idx_avg_thap, 14)

            if E > 0:
                sheet.merge_range(1, idx_salary_start, 1, idx_top_note_col, "BẢNG CHIA LƯƠNG NHÂN VIÊN", f_header_emp)
                for i, e in enumerate(employees):
                    sheet.merge_range(2, idx_salary_start + i, 4, idx_salary_start + i, e.name, f_header_emp)
                sheet.merge_range(2, idx_top_note_col, 4, idx_top_note_col, "Ghi chú Mượn/Cho mượn", f_header_emp)
                sheet.set_column(idx_top_note_col, idx_top_note_col, 45)

            # --- SETUP BOTTOM GRID HEADERS (BẢNG CHẤM CÔNG) ---
            emp_grid_start_row = last_day + 8
            idx_emp_cong_start = 1
            
            for i in range(E):
                sheet.set_column(idx_emp_cong_start + i, idx_emp_cong_start + i, 8) 
                
            idx_emp_bhyt_start = idx_emp_cong_start + E  # BHYT column comes after all cong cols

            if E > 0:
                sheet.merge_range(emp_grid_start_row, idx_emp_cong_start, emp_grid_start_row, idx_emp_bhyt_start, "BẢNG CHẤM CÔNG NHÂN VIÊN", f_header_emp)
                for i, e in enumerate(employees):
                    sheet.merge_range(emp_grid_start_row + 1, idx_emp_cong_start + i, emp_grid_start_row + 2, idx_emp_cong_start + i, e.name, f_header_emp)
                    bhyt_val = "Y" if e.x_has_insurance else "N"
                    sheet.write(emp_grid_start_row + 3, idx_emp_cong_start + i, bhyt_val, f_header_emp)
                sheet.merge_range(emp_grid_start_row + 1, idx_emp_bhyt_start, emp_grid_start_row + 3, idx_emp_bhyt_start, "Đóng\nBHYT", f_header_emp)
                sheet.set_column(idx_emp_bhyt_start, idx_emp_bhyt_start, 8)

            # --- RENDER DATA LOOPS ---
            row_offset = 5 # Day 1 starts at Row 6
            emp_row_offset = emp_grid_start_row + 4 # Day 1 for Matrix Grid starts here
            
            for day in range(1, last_day + 1):
                current_date = date(self.year, int(self.month), day)
                sheet.write(row_offset, 0, day, f_cell_center)
                sheet.write(emp_row_offset, 0, day, f_cell_center)
                
                row_actual = row_offset + 1
                row_emp_actual = emp_row_offset + 1
                
                daily_logs = logs.filtered(lambda l: l.date == current_date)
                daily_pools = pool_results.filtered(lambda p: p.date == current_date)
                
                for i, p in enumerate(products):
                    qty = sum([pl.quantity for log in daily_logs for pl in log.product_line_ids if pl.product_id.id == p.id])
                    sheet.write(row_offset, i + 1, qty or 0, f_cell_center)
                
                # SỐ CÔNG SẢN XUẤT THỰC TẾ CỦA TỔ NÀY (Bao gồm người nhà và người mượn đã duyệt)
                worker_lines = self.env['dl.worker.log.line'].search([
                    ('production_log_id.date', '=', current_date),
                    ('actual_group_id', '=', group.id),
                    ('handshake_status', 'in', ['n/a', 'confirmed']),
                    ('production_log_id.state', 'in', ['confirmed', 'locked'])
                ])
                sc_sx_val = sum(worker_lines.mapped('worked_hours'))
                sheet.write_number(row_offset, idx_sc_sx, sc_sx_val, f_cell_center)

                # TRẢ LƯƠNG NGOÀI: Những người mượn từ tổ khác đến làm cho tổ này
                incoming_logs = self.env['dl.worker.log.line'].search([
                    ('production_log_id.date', '=', current_date),
                    ('actual_group_id', '=', group.id),
                    ('native_group_id', '!=', group.id),
                    ('handshake_status', 'in', ['n/a', 'confirmed']),
                    ('production_log_id.state', 'in', ['confirmed', 'locked'])
                ])
                sc_ngoai_val = sum(incoming_logs.mapped('worked_hours'))
                sheet.write_number(row_offset, idx_sc_ngoai, sc_ngoai_val, f_cell_center)
                
                c_sc_sx = xl_col_to_name(idx_sc_sx)
                c_sc_ngoai = xl_col_to_name(idx_sc_ngoai)
                c_sc_noi_bo = xl_col_to_name(idx_sc_noi_bo)
                c_tra_cao = xl_col_to_name(idx_tra_cao)
                c_tra_thap = xl_col_to_name(idx_tra_thap)
                c_tu_ngoai_cao = xl_col_to_name(idx_tu_ngoai_cao)
                c_tu_ngoai_thap = xl_col_to_name(idx_tu_ngoai_thap)
                c_dt_cao = xl_col_to_name(idx_dt_cao)
                c_dt_thap = xl_col_to_name(idx_dt_thap)

                start_col = xl_col_to_name(1)
                end_col = xl_col_to_name(M) if M > 0 else 'A' 
                sump_cao = f"SUMPRODUCT({start_col}{row_actual}:{end_col}{row_actual}, ${start_col}$4:${end_col}$4)" if M > 0 else "0"
                sump_thap = f"SUMPRODUCT({start_col}{row_actual}:{end_col}{row_actual}, ${start_col}$5:${end_col}$5)" if M > 0 else "0"

                f_tra_cao = f"=IF(${c_sc_sx}{row_actual}=0, 0, ({sump_cao})/${c_sc_sx}{row_actual}*${c_sc_ngoai}{row_actual})"
                f_tra_thap = f"=IF(${c_sc_sx}{row_actual}=0, 0, ({sump_thap})/${c_sc_sx}{row_actual}*${c_sc_ngoai}{row_actual})"
                sheet.write_formula(row_offset, idx_tra_cao, f_tra_cao, f_cell_formula)
                sheet.write_formula(row_offset, idx_tra_thap, f_tra_thap, f_cell_formula)

                # THU TỪ NGOÀI: Người của tổ mình đi làm cho tổ khác
                outgoing_logs = self.env['dl.worker.log.line'].search([
                    ('production_log_id.date', '=', current_date),
                    ('native_group_id', '=', group.id),
                    ('actual_group_id', '!=', group.id),
                    ('handshake_status', 'in', ['n/a', 'confirmed']),
                    ('production_log_id.state', 'in', ['confirmed', 'locked'])
                ])
                dest_group_ids = set(outgoing_logs.mapped('actual_group_id.id'))
                f_tu_cao_parts = []
                f_tu_thap_parts = []
                for dest_id in dest_group_ids:
                    if dest_id not in group_maps: continue
                    dest_map = group_maps[dest_id]
                    sc_to_dest = sum(outgoing_logs.filtered(lambda l: l.actual_group_id.id == dest_id).mapped('worked_hours'))
                    s_name = dest_map['sheet_name']
                    d_c_sc_sx = xl_col_to_name(dest_map['M'] + 1)
                    s_ngoai = dest_map['c_sc_ngoai']
                    p_cao = f"IF({s_name}!${s_ngoai}{row_actual}=0, 0, {s_name}!${dest_map['c_tra_cao']}{row_actual}*({sc_to_dest}/{s_name}!${s_ngoai}{row_actual}))"
                    p_thap = f"IF({s_name}!${s_ngoai}{row_actual}=0, 0, {s_name}!${dest_map['c_tra_thap']}{row_actual}*({sc_to_dest}/{s_name}!${s_ngoai}{row_actual}))"
                    f_tu_cao_parts.append(p_cao)
                    f_tu_thap_parts.append(p_thap)
                
                sheet.write_formula(row_offset, idx_tu_ngoai_cao, f"={'+'.join(f_tu_cao_parts)}" if f_tu_cao_parts else "=0", f_cell_formula)
                sheet.write_formula(row_offset, idx_tu_ngoai_thap, f"={'+'.join(f_tu_thap_parts)}" if f_tu_thap_parts else "=0", f_cell_formula)

                sheet.write_formula(row_offset, idx_dt_cao, f"=({sump_cao}) - ${c_tra_cao}{row_actual} + ${c_tu_ngoai_cao}{row_actual}", f_cell_formula)
                sheet.write_formula(row_offset, idx_dt_thap, f"=({sump_thap}) - ${c_tra_thap}{row_actual} + ${c_tu_ngoai_thap}{row_actual}", f_cell_formula)

                # Write Attendance (Bottom Grid) - plain, no coloring here
                for i, e in enumerate(employees):
                    col_cong = idx_emp_cong_start + i
                    att_lines = self.env['dl.daily.attendance.line'].search([
                        ('date', '=', current_date),
                        ('employee_id', '=', e.id)
                    ])
                    work_days = sum(att_lines.mapped('actual_work'))
                    sheet.write_number(emp_row_offset, col_cong, work_days or 0, f_cell_center)

                # Xây dựng nội dung cột Ghi chú mượn/cho mượn
                note_parts = []
                if incoming_logs:
                    borrow_map = {}
                    for ll in incoming_logs:
                        src_name = ll.native_group_id.name or '?'
                        emp_name = ll.employee_id.name or '?'
                        borrow_map.setdefault(src_name, []).append(emp_name)
                    borrow_parts = ', '.join(
                        f'{emp} - {src}'
                        for src, emps in borrow_map.items()
                        for emp in emps
                    )
                    note_parts.append(f'Mượn: {borrow_parts}')
                if outgoing_logs:
                    lend_map = {}
                    for ll in outgoing_logs:
                        dst_name = ll.actual_group_id.name or '?'
                        emp_name = ll.employee_id.name or '?'
                        lend_map.setdefault(emp_name, []).append(dst_name)
                    lend_parts = ', '.join(
                        f'{emp} -> {dsts[0]}'
                        for emp, dsts in lend_map.items()
                    )
                    note_parts.append(f'Cho mượn: {lend_parts}')
                note_text = '\n'.join(note_parts)

                # Công thức Tổng SC Chấm Công for Top Grid.
                start_cong = xl_col_to_name(idx_emp_cong_start)
                end_cong = xl_col_to_name(idx_emp_cong_start + E - 1)

                if E > 0:
                    sheet.write_formula(row_offset, idx_sc_noi_bo, f"=SUM({start_cong}{row_emp_actual}:{end_cong}{row_emp_actual})", f_cell_formula)
                else:
                    sheet.write(row_offset, idx_sc_noi_bo, 0, f_cell_center)

                # Thu nhập TB Cao/Thấp (Doanh thu ròng / Tổng SC nội bộ)
                c_avg_cao = xl_col_to_name(idx_avg_cao)
                c_avg_thap = xl_col_to_name(idx_avg_thap)
                sheet.write_formula(row_offset, idx_avg_cao, f"=IF(${c_sc_noi_bo}{row_actual}=0, 0, ${c_dt_cao}{row_actual}/${c_sc_noi_bo}{row_actual})", f_cell_formula)
                sheet.write_formula(row_offset, idx_avg_thap, f"=IF(${c_sc_noi_bo}{row_actual}=0, 0, ${c_dt_thap}{row_actual}/${c_sc_noi_bo}{row_actual})", f_cell_formula)

                # Write Salaries for Employees (Top Grid) with color coding
                lent_out_emp_ids = set(outgoing_logs.mapped('employee_id.id'))
                for i, e in enumerate(employees):
                    col_luong = idx_salary_start + i
                    col_cong = idx_emp_cong_start + i
                    c_cong = xl_col_to_name(col_cong)

                    # Lấy đặc điểm công của nhân viên hôm nay
                    att_lines_emp = self.env['dl.daily.attendance.line'].search([
                        ('date', '=', current_date),
                        ('employee_id', '=', e.id)
                    ])
                    work_days_emp = sum(att_lines_emp.mapped('actual_work'))

                    # Chọn định dạng: cam = cho mượn, vàng = nghỉ, vàng nhạt = công < 1, xanh = bình thường
                    if e.id in lent_out_emp_ids:
                        salary_fmt = f_salary_lent_out
                    elif work_days_emp == 0:
                        salary_fmt = f_salary_absent
                    elif work_days_emp < 1:
                        salary_fmt = f_salary_partial
                    else:
                        salary_fmt = f_cell_formula

                    total_cong_row = emp_grid_start_row + 5 + last_day
                    bhyt_row = emp_grid_start_row + 4

                    b_fml = (f"IF(${c_sc_noi_bo}{row_actual}=0, 0, "
                             f'IF(AND(${c_cong}${total_cong_row}>={req_days}, {c_cong}{bhyt_row}="Y"), '
                             f"${c_dt_cao}{row_actual}/${c_sc_noi_bo}{row_actual}*${c_cong}{row_emp_actual}, "
                             f"${c_dt_thap}{row_actual}/${c_sc_noi_bo}{row_actual}*${c_cong}{row_emp_actual}))")
                    sheet.write_formula(row_offset, col_luong, f"={b_fml}", salary_fmt)

                # Ghi chú lên top grid
                sheet.write(row_offset, idx_top_note_col, note_text, f_cell_note)

                row_offset += 1
                emp_row_offset += 1

            # Tổng kết Doanh thu ở Đáy Top Grid
            sheet.write(row_offset, 0, "TỔNG", f_header)
            # Tổng kết đến hết cột lương của nhân viên cuối cùng (idx_top_note_col - 1)
            for i in range(1, idx_top_note_col):
                c_name = xl_col_to_name(i)
                sheet.write_formula(row_offset, i, f"=SUM({c_name}6:{c_name}{row_offset})", f_cell_bold_money)
            # Cột ghi chú ở dòng TỔNG để trống hoặc kẻ khung
            sheet.write(row_offset, idx_top_note_col, "", f_cell_bold_money)

            # Tổng kết Chấm công ở Đáy Bottom Grid
            sheet.write(emp_row_offset, 0, "TỔNG", f_header)
            for i in range(1, E + 1):
                c_name = xl_col_to_name(i)
                sheet.write_formula(emp_row_offset, idx_emp_cong_start - 1 + i, f"=SUM({c_name}{emp_grid_start_row+5}:{c_name}{emp_row_offset})", f_cell_bold_money)

            row_offset = emp_row_offset

            # ================= LOANED LOGS =================
            loaned_results = pool_results.filtered(lambda r: r.is_loaned_worker)
            if loaned_results:
                loaned_results = loaned_results.sorted(key=lambda r: (r.date, r.employee_id.name))
                row_offset += 3
                sheet.merge_range(row_offset, 0, row_offset, 5, "CHI TIẾT MƯỢN NGƯỜI TỪ TỔ KHÁC MANG VỀ TỪNG NGÀY", f_header_emp)
                row_offset += 1
                sheet.write(row_offset, 0, "Ngày", f_header_emp)
                sheet.write(row_offset, 1, "Nhân sự", f_header_emp)
                sheet.write(row_offset, 2, "Tổ đến làm", f_header_emp)
                sheet.write(row_offset, 3, "Số Từng Người", f_header_emp)
                sheet.write(row_offset, 4, "Tiền mang về (Cao)", f_header_emp)
                sheet.write(row_offset, 5, "Tiền mang về (Thấp)", f_header_emp)
                
                row_offset += 1
                start_loanc_row = row_offset + 1
                for r in loaned_results:
                    log_lines = self.env['dl.worker.log.line'].search([
                        ('production_log_id.date', '=', r.date),
                        ('employee_id', '=', r.employee_id.id),
                        ('production_log_id.production_group_id', '!=', group.id),
                        ('production_log_id.state', 'in', ['confirmed', 'locked'])
                    ])
                    # Gom nhóm theo tổ đích để tạo dòng
                    dest_map = {}
                    for ll in log_lines:
                        d_id = ll.production_log_id.production_group_id.id
                        d_name = ll.production_log_id.production_group_id.name
                        if d_id not in dest_map:
                            dest_map[d_id] = {'name': d_name, 'hours': 0}
                        dest_map[d_id]['hours'] += ll.worked_hours

                    for d_id, d_data in dest_map.items():
                        sheet.write(row_offset, 0, r.date.strftime('%d/%m/%Y'), f_cell_center)
                        sheet.write(row_offset, 1, r.employee_id.name, f_cell_center)
                        sheet.write(row_offset, 2, d_data['name'], f_cell_center)
                        sheet.write_number(row_offset, 3, d_data['hours'], f_cell_center)
                        
                        calc_cao = 0
                        calc_thap = 0
                        if d_id in group_maps:
                            sm = group_maps[d_id]
                            sname = sm['sheet_name']
                            s_ng = sm['c_sc_ngoai']
                            drow = r.date.day + 5  # Index corresponds directly to Day. Day 1 is row 6.
                            sc_h = d_data['hours']
                            calc_cao = f"=IF({sname}!${s_ng}{drow}=0, 0, {sname}!${sm['c_tra_cao']}{drow} * ({sc_h} / {sname}!${s_ng}{drow}))"
                            calc_thap = f"=IF({sname}!${s_ng}{drow}=0, 0, {sname}!${sm['c_tra_thap']}{drow} * ({sc_h} / {sname}!${s_ng}{drow}))"
                            sheet.write_formula(row_offset, 4, calc_cao, f_cell_formula)
                            sheet.write_formula(row_offset, 5, calc_thap, f_cell_formula)
                        else:
                            sheet.write(row_offset, 4, 0, f_cell_money)
                            sheet.write(row_offset, 5, 0, f_cell_money)
                        row_offset += 1
                sheet.merge_range(row_offset, 0, row_offset, 2, "TỔNG ĐÁNH THUÊ", f_header)
                sheet.write_formula(row_offset, 3, f"=SUM(D{start_loanc_row}:D{row_offset})", f_cell_bold_money)
                sheet.write_formula(row_offset, 4, f"=SUM(E{start_loanc_row}:E{row_offset})", f_cell_bold_money)
                sheet.write_formula(row_offset, 5, f"=SUM(F{start_loanc_row}:F{row_offset})", f_cell_bold_money)

        if sheets_created == 0:
            sheet = workbook.add_worksheet("Trống")
            sheet.write(0, 0, "Không có dữ liệu hợp lệ trong khoảng thời gian này.")

        workbook.close()
        
        excel_data = base64.b64encode(buffer.getvalue())
        self.write({
            'file_data': excel_data,
            'file_name': f'Bao_Cao_Matrix_Thang_{self.month}_{self.year}.xlsx'
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dl.comprehensive.excel.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }


