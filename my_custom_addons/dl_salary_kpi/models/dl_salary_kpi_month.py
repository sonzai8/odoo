# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from calendar import monthrange
from datetime import date

class SalaryKpiMonth(models.Model):
    _name = 'dl.salary.kpi.month'
    _description = 'Cân đối bảng công tháng'
    _order = 'date_month desc'

    name = fields.Char(string='Tên bản ghi', compute='_compute_name', store=True)
    date_month = fields.Date(string='Tháng/Năm', required=True, default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('lock_normal', 'Chốt công Thường'),
        ('lock_ot', 'Chốt Công Làm thêm'),
        ('lock_regime', 'Chốt Chế Độ'),
        ('lock_kpi', 'Chốt KPI'),
        ('confirmed', 'Xác nhận')
    ], string='Trạng thái', default='draft')
    
    line_ids = fields.One2many('dl.salary.kpi.line', 'month_id', string='Chi tiết chấm công')

    @api.depends('date_month')
    def _compute_name(self):
        for rec in self:
            if rec.date_month:
                rec.name = f"Bảng công tháng {rec.date_month.strftime('%m/%Y')}"
            else:
                rec.name = "Mới"

    # Các trường báo cáo nhanh
    total_employees = fields.Integer(string="Tổng nhân viên", compute="_compute_quick_stats")
    total_n = fields.Float(string="Tổng Công Ngày", compute="_compute_quick_stats")
    total_d = fields.Float(string="Tổng Công Đêm", compute="_compute_quick_stats")
    total_p = fields.Float(string="Tổng Ngày Phép", compute="_compute_quick_stats")
    total_pl = fields.Float(string="Tổng Ngày Lễ", compute="_compute_quick_stats")
    total_kp = fields.Float(string="Tổng Không phép (KP)", compute="_compute_quick_stats")
    total_o = fields.Float(string="Tổng Nghỉ ốm (Ô)", compute="_compute_quick_stats")
    total_dc = fields.Float(string="Tổng Đổi ca (ĐC)", compute="_compute_quick_stats")
    total_co = fields.Float(string="Tổng Con ốm (CÔ)", compute="_compute_quick_stats")
    
    attendance_summary_html = fields.Html(string="Tổng hợp mã công", compute="_compute_quick_stats")

    @api.depends('line_ids', 'line_ids.day_01', 'line_ids.day_02', 'line_ids.day_03', 'line_ids.day_04', 'line_ids.day_05',
                 'line_ids.day_06', 'line_ids.day_07', 'line_ids.day_08', 'line_ids.day_09', 'line_ids.day_10',
                 'line_ids.day_11', 'line_ids.day_12', 'line_ids.day_13', 'line_ids.day_14', 'line_ids.day_15',
                 'line_ids.day_16', 'line_ids.day_17', 'line_ids.day_18', 'line_ids.day_19', 'line_ids.day_20',
                 'line_ids.day_21', 'line_ids.day_22', 'line_ids.day_23', 'line_ids.day_24', 'line_ids.day_25',
                 'line_ids.day_26', 'line_ids.day_27', 'line_ids.day_28', 'line_ids.day_29', 'line_ids.day_30', 'line_ids.day_31')
    def _compute_quick_stats(self):
        for rec in self:
            rec.total_employees = len(rec.line_ids)
            n, d, p, pl, kp, o, dc, co = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            
            try:
                # Đếm chi tiết từng loại mã
                code_counts = {}
                
                for line in rec.line_ids:
                    for i in range(1, 32):
                        att = getattr(line, f'day_{i:02d}')
                        if att:
                            code = att.code
                            name = att.name
                            key = (code, name)
                            code_counts[key] = code_counts.get(key, 0) + 1
                            
                            # Thống kê nhanh cho các nhóm chính
                            if code == 'N': n += 1.0
                            elif code in ['N/1', 'N/2']: n += 0.5
                            elif code == 'Đ': d += 1.0
                            elif code in ['Đ/1', 'Đ/2']: d += 0.5
                            elif code == 'P': p += 1.0
                            elif code == 'PL': pl += 1.0
                            elif code == 'KP': kp += 1.0
                            elif code == 'Ô': o += 1.0
                            elif code == 'ĐC': dc += 1.0
                            elif code == 'CÔ': co += 1.0
            
            except Exception:
                # Nếu bị lỗi (do đang nâng cấp database chưa có cột), gán giá trị mặc định 0
                rec.attendance_summary_html = ""
                rec.total_n = 0
                rec.total_d = 0
                rec.total_p = 0
                rec.total_pl = 0
                rec.total_kp = 0
                rec.total_o = 0
                rec.total_dc = 0
                rec.total_co = 0
                continue

            rec.total_n = n
            rec.total_d = d
            rec.total_p = p
            rec.total_pl = pl
            rec.total_kp = kp
            rec.total_o = o
            rec.total_dc = dc
            rec.total_co = co
            
            # Tạo bảng HTML
            html = '<table class="table table-sm table-bordered mt-2">'
            html += '<thead class="bg-light"><tr><th>Mã</th><th>Tên loại công</th><th>Số lượng (ô)</th></tr></thead><tbody>'
            
            # Sắp xếp theo mã
            sorted_keys = sorted(code_counts.keys(), key=lambda x: x[0])
            for key in sorted_keys:
                html += f'<tr><td><strong>{key[0]}</strong></td><td>{key[1]}</td><td>{code_counts[key]}</td></tr>'
            
            html += '</tbody></table>'
            rec.attendance_summary_html = html

    @api.model_create_multi
    def create(self, vals_list):
        """Khi tạo mới, tự động lấy toàn bộ nhân viên và chấm công mặc định"""
        records = super(SalaryKpiMonth, self).create(vals_list)
        for rec in records:
            rec._auto_load_employees()
        return records

    def _auto_load_employees(self):
        """Logic lấy toàn bộ nhân viên active và chấm công mặc định N (T2-T7)"""
        hr_employees = self.env['hr.employee'].search([('active', '=', True)])
        att_type_n = self.env['dl.salary.kpi.attendance.type'].search([('code', '=', 'N')], limit=1)
        
        last_day = monthrange(self.date_month.year, self.date_month.month)[1]
        
        lines = []
        for emp in hr_employees:
            vals = {
                'employee_id': emp.id,
                'identification_id': emp.identification_id,
                'month_id': self.id,
            }
            # Thiết lập chấm công mặc định N cho Thứ 2 - Thứ 7
            if att_type_n:
                for day in range(1, last_day + 1):
                    d = date(self.date_month.year, self.date_month.month, day)
                    if d.weekday() < 6:
                        vals[f'day_{day:02d}'] = att_type_n.id
            lines.append(vals)
        
        if lines:
            self.env['dl.salary.kpi.line'].create(lines)

    @api.model
    def get_views(self, views, options=None):
        res = super().get_views(views, options)
        if 'form' in res['views']:
            from lxml import etree
            from datetime import date
            import calendar
            
            arch = etree.fromstring(res['views']['form']['arch'])
            
            # Lấy thông tin tháng từ context hoặc record hiện tại
            # Vì get_views là static, ta dùng logic mặc định hoặc lấy từ default_date_month
            # Thực tế: Khi người dùng mở form, Odoo gọi get_views.
            # Ta có thể thử lấy tháng từ context.
            ctx = self.env.context
            date_month_str = ctx.get('default_date_month') or fields.Date.today().strftime('%Y-%m-01')
            try:
                d_m = fields.Date.from_string(date_month_str)
            except:
                d_m = fields.Date.today()
                
            weekday_map = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
            year, month = d_m.year, d_m.month
            
            for i in range(1, 32):
                weekday_label = ""
                is_sunday = False
                try:
                    d = date(year, month, i)
                    weekday_label = f"{i:02d} - {weekday_map[d.weekday()]}"
                    is_sunday = (d.weekday() == 6)
                except ValueError:
                    weekday_label = f"{i:02d}"

                # Cập nhật Label cho cả công thường và OT
                for field_name in [f"day_{i:02d}", f"ot_day_{i:02d}"]:
                    nodes = arch.xpath(f"//field[@name='{field_name}']")
                    for node in nodes:
                        node.set('string', weekday_label)
                        
                        # Thêm class cho Chủ Nhật
                        classes = node.get('class', '').split()
                        if is_sunday:
                            classes.append('kpi_sunday_col')
                        node.set('class', ' '.join(set(classes)))
                        
                        # Decorations (chỉ cho công thường)
                        if field_name.startswith('day_'):
                            code_field = f"{field_name}_code"
                            node.set('decoration-warning', f"{code_field} == 'CP'")
                            node.set('decoration-danger', f"{code_field} in ['KP', 'Ô']")
                            node.set('decoration-bf', f"{code_field} == 'ĐC'")
                        
                        # Chỉ cho phép chấm công làm thêm vào ngày Chủ Nhật
                        if field_name.startswith('ot_day_'):
                            if not is_sunday:
                                node.set('readonly', '1')
                                node.set('force_save', '1')

            res['views']['form']['arch'] = etree.tostring(arch, encoding='unicode')



        return res


    def action_lock_normal(self):
        # Khi chốt công thường, xoá sạch dữ liệu công làm thêm cũ để tránh sai lệch dữ liệu
        # Đảm bảo khi sang bước Làm thêm, dữ liệu sẽ được tính/nhập mới hoàn toàn
        for line in self.line_ids:
            ot_vals = {}
            for i in range(1, 32):
                ot_vals[f'ot_day_{i:02d}'] = False
            line.write(ot_vals)
            
        self.write({'state': 'lock_normal'})

    def action_lock_ot(self):
        self.write({'state': 'lock_ot'})

    def action_lock_regime(self):
        self.write({'state': 'lock_regime'})

    def action_lock_kpi(self):
        self.write({'state': 'lock_kpi'})

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    # Các hàm quay lại trạng thái trước
    def action_back_to_draft(self):
        self.write({'state': 'draft'})

    def action_back_to_lock_normal(self):
        self.write({'state': 'lock_normal'})

    def action_back_to_lock_ot(self):
        self.write({'state': 'lock_ot'})

    def action_back_to_lock_regime(self):
        self.write({'state': 'lock_regime'})

    def action_back_to_lock_kpi(self):
        self.write({'state': 'lock_kpi'})

    def action_draft(self):
        # Giữ lại hàm này để tương thích nếu cần, hoặc xoá nếu muốn ép quy trình quay lại từng bước
        self.write({'state': 'draft'})

    def _action_init_overtime_suggestions(self):
        """Khởi tạo dữ liệu gợi ý công làm thêm dựa trên công thường cho các ngày Chủ Nhật"""
        from datetime import date
        att_types = self.env['dl.salary.kpi.attendance.type'].search([('apply_to', 'in', ['overtime', 'both'])])
        n_ot = att_types.filtered(lambda t: t.code == '0.5N')
        d_ot = att_types.filtered(lambda t: t.code == '0.5Đ')
        
        month_date = self.date_month
        year, month = month_date.year, month_date.month
        
        for line in self.line_ids:
            vals = {}
            for i in range(1, 32):
                field_name = f'ot_day_{i:02d}'
                # Chỉ gợi ý cho ngày Chủ Nhật và nếu ô đó đang trống
                try:
                    # Gợi ý cho tất cả các ngày (khớp với logic trong Excel export)
                    if not getattr(line, field_name):
                        norm_att = getattr(line, f'day_{i:02d}')
                        if norm_att:
                            if norm_att.code == 'N' and n_ot:
                                vals[field_name] = n_ot[0].id
                            elif norm_att.code == 'Đ' and d_ot:
                                vals[field_name] = d_ot[0].id
                except ValueError:
                    pass
            if vals:
                line.write(vals)

    def action_export_excel(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/dl_salary_kpi/export_attendance/{self.id}',
            'target': 'new',
        }

    def action_import_excel(self):
        self.ensure_one()
        return {
            'name': 'Nhập/Xuất Công Thường',
            'type': 'ir.actions.act_window',
            'res_model': 'dl.salary.kpi.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_month_id': self.id, 'default_wizard_type': 'normal'}
        }

    def action_import_ot_excel(self):
        self.ensure_one()
        return {
            'name': 'Nhập/Xuất Công Làm Thêm',
            'type': 'ir.actions.act_window',
            'res_model': 'dl.salary.kpi.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_month_id': self.id, 'default_wizard_type': 'overtime'}
        }

    def action_export_ot_excel(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/dl_salary_kpi/export_ot_attendance/{self.id}',
            'target': 'new',
        }
