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
