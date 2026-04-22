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
                field_name = f"day_{i:02d}"
                code_field = f"day_{i:02d}_code"
                nodes = arch.xpath(f"//field[@name='{field_name}']")
                for node in nodes:
                    try:
                        d = date(year, month, i)
                        wd = weekday_map[d.weekday()]
                        # Gán label mới: "01\n T2"
                        node.set('string', f"{i:02d}\n{wd}")
                        
                        # Thêm decorations cho mã công
                        node.set('decoration-warning', f"{code_field} == 'CP'")
                        node.set('decoration-danger', f"{code_field} in ['KP', 'Ô']")
                        node.set('decoration-bf', f"{code_field} == 'ĐC'") # Dùng bf làm marker cho Tím
                        
                        # Thêm class cho Chủ Nhật
                        classes = node.get('class', '').split()
                        if d.weekday() == 6:
                            classes.append('kpi_sunday_col')
                        node.set('class', ' '.join(set(classes)))
                        
                    except ValueError:
                        node.set('string', f"{i:02d}")

            res['views']['form']['arch'] = etree.tostring(arch, encoding='unicode')



        return res


    def action_lock_normal(self):
        self.write({'state': 'lock_normal'})

    def action_lock_ot(self):
        self.write({'state': 'lock_ot'})

    def action_lock_regime(self):
        self.write({'state': 'lock_regime'})

    def action_lock_kpi(self):
        self.write({'state': 'lock_kpi'})

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_draft(self):
        self.write({'state': 'draft'})

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
            'name': 'Nhập bảng công từ Excel',
            'type': 'ir.actions.act_window',
            'res_model': 'dl.salary.kpi.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_month_id': self.id}
        }
