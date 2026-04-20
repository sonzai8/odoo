# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SalaryKpiMonth(models.Model):
    _name = 'dl.salary.kpi.month'
    _description = 'Cân đối lương & KPI theo tháng'
    _order = 'date_month desc'

    name = fields.Char(string='Tên bản ghi', compute='_compute_name', store=True)
    date_month = fields.Date(string='Tháng/Năm', required=True, default=fields.Date.today)
    company_revenue = fields.Monetary(string='Doanh thu công ty', currency_field='currency_id')
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('confirmed', 'Đã xác nhận')
    ], string='Trạng thái', default='draft')
    
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    meal_allowance_default = fields.Monetary(string='Mặc định Ăn ca', default=650000.0, currency_field='currency_id')
    women_allowance_default = fields.Monetary(string='Mặc định Trợ cấp phụ nữ', default=500000.0, currency_field='currency_id')
    line_ids = fields.One2many('dl.salary.kpi.line', 'month_id', string='Chi tiết lương & KPI')

    @api.depends('date_month')
    def _compute_name(self):
        for rec in self:
            if rec.date_month:
                rec.name = f"Tháng {rec.date_month.strftime('%m/%Y')}"
            else:
                rec.name = "Mới"

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_load_employees(self):
        self.ensure_one()
        from calendar import monthrange
        
        # Auto-sync active HR employees to KPI employees first
        hr_employees = self.env['hr.employee'].search([('active', '=', True)])
        existing_kpi_mapped_ids = self.env['dl.salary.kpi.employee'].search([('employee_id', '!=', False)]).mapped('employee_id').ids
        for emp in hr_employees:
            if emp.id not in existing_kpi_mapped_ids:
                self.env['dl.salary.kpi.employee'].create({
                    'name': emp.name,
                    'employee_id': emp.id,
                    'identification_id': emp.identification_id,
                    'department_id': emp.department_id.id,
                    'work_group_id': emp.x_source_group_id.id,
                })

        # Now load from kpi employees
        kpi_employees = self.env['dl.salary.kpi.employee'].search([('active', '=', True)])
        last_day = monthrange(self.date_month.year, self.date_month.month)[1] if self.date_month else 30
        
        new_count = 0
        updated_count = 0
        
        for k_emp in kpi_employees:
            # Check if kpi_employee already has a line or if a manual line matches the name
            existing_line = self.line_ids.filtered(lambda l: l.kpi_employee_id == k_emp)
            if not existing_line:
                # Try matching by name if kpi_employee matches (case manual input before sync)
                existing_line = self.line_ids.filtered(lambda l: not l.kpi_employee_id and l.employee_name == k_emp.name)
            
            if existing_line:
                # Update existing line details
                write_vals = {
                    'kpi_employee_id': k_emp.id,
                    'employee_name': k_emp.name,
                    'identification_id': k_emp.identification_id,
                    'department_id': k_emp.department_id.id,
                    'work_group_id': k_emp.work_group_id.id,
                    'meal_allowance': self.meal_allowance_default,
                    'women_allowance': self.women_allowance_default if k_emp.gender == 'female' else 0.0,
                }
                existing_line.write(write_vals)
                updated_count += 1
            else:
                # Create new line
                att_lines = []
                if k_emp.default_att_type_id:
                    for day in range(1, last_day + 1):
                        att_lines.append((0, 0, {
                            'day': day,
                            'attendance_type_id': k_emp.default_att_type_id.id
                        }))
                
                self.write({'line_ids': [(0, 0, {
                    'kpi_employee_id': k_emp.id,
                    'employee_name': k_emp.name,
                    'identification_id': k_emp.identification_id,
                    'department_id': k_emp.department_id.id,
                    'work_group_id': k_emp.work_group_id.id,
                    'meal_allowance': self.meal_allowance_default,
                    'women_allowance': self.women_allowance_default if k_emp.gender == 'female' else 0.0,
                    'attendance_ids': att_lines
                })]})
                new_count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Hoàn tất',
                'message': 'Đã tải mới %s và cập nhật %s nhân viên.' % (new_count, updated_count),
                'type': 'info' if new_count + updated_count > 0 else 'warning',
            }
        }

    def action_export_attendance_template(self):
        self.ensure_one()
        import io
        import base64
        from calendar import monthrange
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        except ImportError:
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Cham cong"

        # Styles
        header_font = Font(name='Times New Roman', size=14, bold=True)
        base_font = Font(name='Times New Roman', size=14)
        alignment_center = Alignment(horizontal='center', vertical='center')
        border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        weekend_fill = PatternFill(start_color='92D050', end_color='92D050', fill_type='solid') # Xanh lá như ảnh

        # Header STT, Họ tên, CCCD, Xưởng, Tổ
        headers = ["STT", "Họ và tên", "CCCD", "Xưởng", "Tổ biên chế"]
        for col, text in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=text)
            cell.font = header_font
            cell.alignment = alignment_center
            cell.border = border
            ws.column_dimensions[cell.column_letter].width = 25 if text == "Họ và tên" else 15

        # Header Days
        last_day = monthrange(self.date_month.year, self.date_month.month)[1] if self.date_month else 31
        for day in range(1, last_day + 1):
            col = len(headers) + day
            cell = ws.cell(row=1, column=col, value=f"{day:02d}")
            cell.font = header_font
            cell.alignment = alignment_center
            cell.border = border
            ws.column_dimensions[cell.column_letter].width = 5
            
            # Check if Sunday
            dt = self.date_month.replace(day=day)
            if dt.weekday() == 6: # Sunday
                cell.fill = weekend_fill

        # Data
        row = 2
        sorted_lines = self.line_ids.sorted(key=lambda l: (
            l.is_disabled, 
            l.department_id.name or '', 
            l.work_group_id.name or '', 
            l.employee_name or ''
        ))
        for i, line in enumerate(sorted_lines, 1):
            ws.row_dimensions[row].height = 25
            # Basic info
            ws.cell(row=row, column=1, value=i).font = base_font
            ws.cell(row=row, column=2, value=line.employee_name).font = base_font
            ws.cell(row=row, column=3, value=line.identification_id).font = base_font
            ws.cell(row=row, column=4, value=line.department_id.name).font = base_font
            ws.cell(row=row, column=5, value=line.work_group_id.name).font = base_font
            
            for col in range(1, 6):
                ws.cell(row=row, column=col).border = border
                ws.cell(row=row, column=col).alignment = alignment_center

            # Attendance
            att_map = {att.day: (att.attendance_type_id.code or '') for att in line.attendance_ids}
            for day in range(1, last_day + 1):
                col = len(headers) + day
                cell = ws.cell(row=row, column=col, value=att_map.get(day, ''))
                cell.font = base_font
                cell.alignment = alignment_center
                cell.border = border
                
                # Weekend color for data row too?
                dt = self.date_month.replace(day=day)
                if dt.weekday() == 6:
                    cell.fill = weekend_fill
            row += 1

        output = io.BytesIO()
        wb.save(output)
        file_data = base64.b64encode(output.getvalue())
        output.close()

        filename = f"Mau_Cham_Cong_{self.name}.xlsx"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': file_data,
            'store_fname': filename,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

    def action_import_attendance(self):
        self.ensure_one()
        return {
            'name': 'Nhập chấm công KPI',
            'type': 'ir.actions.act_window',
            'res_model': 'dl.salary.kpi.import.attendance.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_month_id': self.id}
        }

    def action_sync_hr_from_month(self):
        self.ensure_one()
        # Trigger sync from employee model
        res = self.env['dl.salary.kpi.employee'].action_sync_from_hr()
        return res

    def action_export_salary_report(self):
        self.ensure_one()
        return {
            'name': 'Đang chuẩn bị báo cáo',
            'type': 'ir.actions.act_window',
            'res_model': 'dl.salary.kpi.export.loading',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_month_id': self.id}
        }

    def _generate_excel_report(self):
        import openpyxl
        import io
        import os
        import logging
        from datetime import datetime

        _logger = logging.getLogger(__name__)
        _logger.info("Starting Excel export for month ID: %s", self.id)

        try:
            from openpyxl.formula.translate import Translator
            from copy import copy
            # Load template using absolute path
            addon_dir = os.path.dirname(os.path.dirname(__file__))
            template_path = os.path.join(addon_dir, 'static', 'xlsx', 'TEMPLATE_DL_SALARY_KPI.xlsx')
            
            if not os.path.exists(template_path):
                _logger.error("Template not found: %s", template_path)
                raise FileNotFoundError(f"Template not found at {template_path}")
                
            wb = openpyxl.load_workbook(template_path)
            sheet = wb.active
            
            # 1. Identify merged ranges involving row 9 to replicate them later
            horizontal_merges = []
            merge_base_map = {} # Maps col to start_col for current row
            for mr in sheet.merged_cells.ranges:
                if mr.min_row <= 9 <= mr.max_row:
                    horizontal_merges.append((mr.min_col, mr.max_col))
                    for c in range(mr.min_col, mr.max_col + 1):
                        merge_base_map[c] = mr.min_col

            # Helper to find the master cell of a merged range in CURRENT row
            def get_fast_base_cell(r, c):
                base_c = merge_base_map.get(c, c)
                return sheet.cell(row=r, column=base_c)

            # 2. Pre-collect ALL cell properties from row 9
            master_row_height = sheet.row_dimensions[9].height
            max_col = sheet.max_column
            if max_col > 200: max_col = 200 
            
            master_data = []
            for col in range(1, max_col + 1):
                src_cell = sheet.cell(row=9, column=col)
                # Capture everything as deeply as possible
                style_dict = {
                    'font': copy(src_cell.font),
                    'border': copy(src_cell.border),
                    'fill': copy(src_cell.fill),
                    'number_format': src_cell.number_format,
                    'protection': copy(src_cell.protection),
                    'alignment': copy(src_cell.alignment),
                }
                master_data.append((src_cell.value, style_dict))

            # 3. Fill Header cells safely
            today = datetime.now()
            def set_header_val(coord, val):
                cell = sheet[coord]
                if cell.__class__.__name__ == 'MergedCell':
                    for mr in sheet.merged_cells.ranges:
                        if coord in mr:
                            sheet.cell(row=mr.min_row, column=mr.min_col).value = val
                            return
                else:
                    cell.value = val

            set_header_val('A3', f"Ngày {today.day:02d} tháng {today.month:02d} Năm {today.year}")
            set_header_val('F4', self.company_revenue)
            if self.date_month:
                set_header_val('KL4', str(self.date_month.month))
                set_header_val('OP4', str(self.date_month.year))
            
            # 4. Fill data rows starting from 10
            current_row = 10
            for line in self.line_ids:
                if line.is_disabled:
                    continue
                
                # a. Replicate row height
                if master_row_height:
                    sheet.row_dimensions[current_row].height = master_row_height

                # b. Replicate merging for this row
                for min_c, max_c in horizontal_merges:
                    sheet.merge_cells(start_row=current_row, start_column=min_c, 
                                      end_row=current_row, end_column=max_c)

                # c. Apply values and styles to EVERY cell
                for col_idx, (val, style) in enumerate(master_data, 1):
                    cell = sheet.cell(row=current_row, column=col_idx)
                    
                    # Apply translated value if not a merged cell (or if it's the base)
                    if cell.__class__.__name__ != 'MergedCell':
                        final_val = val
                        if isinstance(val, str) and val.startswith('='):
                            try:
                                final_val = Translator(val, origin="A9").translate_formula(f"A{current_row}")
                            except Exception:
                                final_val = val
                        cell.value = final_val
                        
                    # Apply style to EVERY cell (regardless of merging)
                    if style:
                        try:
                            # Use copy() to ensure no side effects in openpyxl indexing
                            cell.font = copy(style['font'])
                            cell.border = copy(style['border'])
                            cell.fill = copy(style['fill'])
                            cell.number_format = style['number_format']
                            cell.protection = copy(style['protection'])
                            cell.alignment = copy(style['alignment'])
                        except Exception:
                            pass
                
                # d. Fill specific employee data (using prioritized base cells)
                get_fast_base_cell(current_row, 2).value = line.employee_name
                
                birthday = ""
                if line.kpi_employee_id.employee_id and line.kpi_employee_id.employee_id.birthday:
                    birthday = line.kpi_employee_id.employee_id.birthday.strftime('%d/%m/%Y')
                get_fast_base_cell(current_row, 4).value = birthday
                
                gender_vn = "Nam" if line.gender == 'male' else "Nữ" if line.gender == 'female' else ""
                get_fast_base_cell(current_row, 5).value = gender_vn
                get_fast_base_cell(current_row, 6).value = line.work_group_id.name if line.work_group_id else ""
                
                current_row += 1
                
            # Buffer and return
            fp = io.BytesIO()
            wb.save(fp)
            return fp.getvalue()
            
        except Exception as e:
            _logger.exception("Error in Excel generation for Month %s", self.id)
            raise e
