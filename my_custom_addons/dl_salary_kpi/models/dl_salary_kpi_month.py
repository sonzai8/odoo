# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
from calendar import monthrange
import base64
import io
import copy
from odoo.tools import file_path
import time
import logging
import math
import random

from . import attendance_logic
from . import payroll_logic
from . import kpi_export_logic

_logger = logging.getLogger(__name__)

try:
    from openpyxl import load_workbook
    from openpyxl.cell.cell import MergedCell
    from openpyxl.formula.translate import Translator
except ImportError:
    load_workbook = None

class SalaryKpiMonth(models.Model):
    _name = 'dl.salary.kpi.month'
    _description = 'Cân đối bảng công tháng'
    _order = 'date_month desc'

    name = fields.Char(string='Tên bản ghi', compute='_compute_name', store=True)
    date_month = fields.Date(string='Tháng/Năm', required=True, default=fields.Date.today)
    
    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', related='company_id.currency_id')
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('lock_normal', 'Chốt công Thường'),
        ('lock_ot', 'Chốt Công Làm thêm'),
        ('lock_regime', 'Chốt Chế Độ'),
        ('lock_kpi', 'Chốt KPI'),
        ('confirmed', 'Xác nhận')
    ], string='Trạng thái', default='draft')
    
    line_ids = fields.One2many('dl.salary.kpi.line', 'month_id', string='Chi tiết chấm công')
    
    # Thông tin cân đối tài chính
    dl_revenue = fields.Monetary(string="Doanh thu tháng", currency_field='currency_id')
    dl_production_volume = fields.Float(string="Sản lượng tháng (m³)")
    dl_meal_allowance = fields.Monetary(string="Tiền ăn ca", currency_field='currency_id', default=650000)
    dl_women_allowance = fields.Monetary(string="Phụ cấp phụ nữ", currency_field='currency_id', default=500000)
    
    # Các khoản thưởng áp dụng trong tháng
    bonus_line_ids = fields.Many2many('dl.salary.kpi.bonus.line', string='Các khoản thưởng trong tháng', compute='_compute_bonus_lines')

    line_domain = fields.Char(compute='_compute_line_domain', readonly=True)

    # === Trường lọc tạm thời ===
    filter_employee_name = fields.Char(string='Tìm theo tên', store=False)
    filter_department_id = fields.Many2one('dl.tax.department', string='Lọc phòng ban', store=False)
    filter_position = fields.Char(string='Lọc chức vụ', store=False)
    filtered_line_ids = fields.One2many(
        'dl.salary.kpi.line',
        compute='_compute_filtered_line_ids',
        inverse='_inverse_filtered_line_ids',
        string='Danh sách đã lọc'
    )

    anomaly_line_ids = fields.One2many(
        'dl.salary.kpi.line',
        compute='_compute_anomaly_line_ids',
        string='Dữ liệu bất thường'
    )

    @api.depends('filter_employee_name', 'filter_department_id', 'filter_position')
    def _compute_line_domain(self):
        # Giữ lại logic domain để dùng nếu cần, nhưng ưu tiên filtered_line_ids
        for record in self:
            domain = []
            if record.filter_employee_name:
                domain.append(('employee_name', 'ilike', record.filter_employee_name))
            if record.filter_department_id:
                domain.append(('dl_tax_department_id', '=', record.filter_department_id.id))
            if record.filter_position:
                domain.append(('dl_tax_position', 'ilike', record.filter_position))
            record.line_domain = str(domain)

    @api.depends('line_ids', 'line_ids.employee_name', 'line_ids.dl_tax_department_id', 'line_ids.dl_tax_position',
                 'filter_employee_name', 'filter_department_id', 'filter_position')
    def _compute_filtered_line_ids(self):
        """Trả về danh sách line_ids đã được lọc theo các tiêu chí tạm thời."""
        for record in self:
            lines = record.line_ids
            if record.filter_employee_name:
                keyword = record.filter_employee_name.lower()
                lines = lines.filtered(lambda l: keyword in (l.employee_name or '').lower())
            if record.filter_department_id:
                dept_id = record.filter_department_id
                lines = lines.filtered(lambda l: l.dl_tax_department_id == dept_id)
            if record.filter_position:
                keyword = record.filter_position.lower()
                lines = lines.filtered(lambda l: keyword in (l.dl_tax_position or '').lower())
            record.filtered_line_ids = lines

    def _inverse_filtered_line_ids(self):
        """Đồng bộ thay đổi từ danh sách đã lọc ngược lại line_ids gốc."""
        for record in self:
            # Odoo tự động xử lý cập nhật field trên record con. 
            # Chúng ta chỉ cần đảm bảo line_ids chứa các record mới nếu có.
            actual_line_ids = record.line_ids.ids
            for line in record.filtered_line_ids:
                if line.id not in actual_line_ids:
                    # Nếu có thêm mới record từ view đã lọc (hiếm khi xảy ra ở đây)
                    record.line_ids |= line

    @api.depends(
        'line_ids',
        'line_ids.payroll_net_salary',
        'line_ids.payroll_internal_salary',
        'line_ids.dl_tax_base_salary'
    )
    def _compute_anomaly_line_ids(self):
        """
        Lọc danh sách nhân viên có dữ liệu bất thường:
        - Lương trong (Ln) >= (Lương cơ bản + Lương cơ bản * 0.4).
        - Thực lĩnh ngoài bị âm (Lk < 0).
        - Thực lĩnh ngoài (Lk) > Lương trong (Ln).
        """
        for rec in self:
            anomalies = self.env['dl.salary.kpi.line']
            if rec.line_ids:
                anomalies = rec.line_ids.filtered(
                    lambda l: (l.payroll_net_salary_base > 0 and l.payroll_internal_salary >= (l.payroll_net_salary_base * 1.4))
                    or l.payroll_net_salary_base < 0
                    or (l.payroll_internal_salary > 0 and l.payroll_net_salary_base > l.payroll_internal_salary)
                )
            rec.anomaly_line_ids = anomalies

    def action_clear_payroll_filters(self):
        """Xóa các bộ lọc trong tab Tổng Hợp Công - Lương."""
        self.ensure_one()
        self.write({
            'filter_employee_name': False,
            'filter_department_id': False,
            'filter_position': False,
        })
        return True

    def _compute_bonus_lines(self):
        for rec in self:
            if not rec.date_month:
                rec.bonus_line_ids = False
                continue
            
            year = rec.date_month.year
            month = rec.date_month.month
            
            # Tìm cấu hình thưởng của năm
            bonus_year = self.env['dl.salary.kpi.bonus.year'].search([('year', '=', year), ('active', '=', True)], limit=1)
            if bonus_year:
                # Lọc các dòng thưởng có tháng trùng với tháng đang cân đối
                lines = bonus_year.line_ids.filtered(lambda l: l.date.month == month and l.active)
                rec.bonus_line_ids = [(6, 0, lines.ids)]
            else:
                rec.bonus_line_ids = False

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

    # === Tổng lương toàn bộ (dùng để hiển thị phía trên danh sách, tính từ TẤT CẢ line_ids) ===
    total_lk = fields.Monetary(
        string='Tổng Thực lĩnh ngoài (Lk)',
        compute='_compute_salary_totals',
        currency_field='currency_id',
        help="Tổng Thực lĩnh ngoài (Lk) của toàn bộ nhân viên trong tháng."
    )
    total_ln = fields.Monetary(
        string='Tổng Lương trong (Ln)',
        compute='_compute_salary_totals',
        currency_field='currency_id',
        help="Tổng Lương trong (Ln) nhập tay của toàn bộ nhân viên trong tháng."
    )
    total_bank_transfer = fields.Monetary(
        string='Tổng Tiền chuyển khoản',
        compute='_compute_salary_totals',
        currency_field='currency_id',
        help="Tổng tiền chuyển khoản của toàn bộ nhân viên."
    )

    @api.depends(
        'line_ids.payroll_net_salary_base',
        'line_ids.payroll_internal_salary',
        'line_ids.payroll_bank_transfer_amount',
    )
    def _compute_salary_totals(self):
        """Tính tổng các chỉ số lương chính từ toàn bộ line_ids (không phân trang)."""
        for rec in self:
            rec.total_lk = sum(rec.line_ids.mapped('payroll_net_salary_base'))
            rec.total_ln = sum(rec.line_ids.mapped('payroll_internal_salary'))
            rec.total_bank_transfer = sum(rec.line_ids.mapped('payroll_bank_transfer_amount'))



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
        """Logic lấy toàn bộ nhân viên active (chưa nghỉ việc trước tháng này) và chấm công mặc định N (T2-T7)"""
        first_day = self.date_month.replace(day=1)
        domain = [
            ('active', '=', True),
            '|',
            ('dl_departure_date', '=', False),
            ('dl_departure_date', '>=', first_day)
        ]
        hr_employees = self.env['hr.employee'].search(domain)
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
            arch = etree.fromstring(res['views']['form']['arch'])
            
            # Tiêu đề danh sách chỉ hiện số ngày để không bị lệch khi xem các tháng khác nhau
            for i in range(1, 32):
                label = f"{i:02d}"
                for field_name in [f"day_{i:02d}", f"ot_day_{i:02d}"]:
                    nodes = arch.xpath(f"//field[@name='{field_name}']")
                    for node in nodes:
                        node.set('string', label)
            
            res['views']['form']['arch'] = etree.tostring(arch, encoding='unicode')
        return res

    def action_recompute_all_data(self):
        """Ép buộc tính toán lại toàn bộ dữ liệu thống kê và lương chi tiết."""
        import time
        t_start = time.time()
        
        att_type_n = self.env['dl.salary.kpi.attendance.type'].search([('code', '=', 'N')], limit=1)
        
        for rec in self:
            # 1. Ép buộc Odoo tính toán lại các trường computed trong các dòng con
            if rec.line_ids:
                t3 = time.time()
                
                # Tính toán lại tổng công
                
                # Tính toán lại tổng công
                rec.line_ids._compute_totals()
                t4 = time.time()
                _logger.info("=== BENCHMARK CHỐT CÔNG [%s]: _compute_totals mất %.2fs ===", rec.name, t4 - t3)
                
                rec.line_ids._compute_payroll_internal()
                t5 = time.time()
                _logger.info("=== BENCHMARK CHỐT CÔNG [%s]: _compute_payroll_internal mất %.2fs ===", rec.name, t5 - t4)
            else:
                t5 = time.time()
            
            # 2. Tính toán lại thống kê nhanh
            rec._compute_quick_stats()
            t6 = time.time()
            _logger.info("=== BENCHMARK CHỐT CÔNG [%s]: _compute_quick_stats mất %.2fs ===", rec.name, t6 - t5)
            
        t_end = time.time()
        _logger.info("=== BENCHMARK CHỐT CÔNG TỔNG CỘNG MẤT %.2fs ===", t_end - t_start)
        return True

    def action_lock_normal(self):
        # Khi chốt công thường, tự động khởi tạo gợi ý công làm thêm (0.5N/0.5Đ)
        # dựa trên các ngày đã chấm công thường (N/Đ).
        self._action_init_overtime_suggestions()
            
        self.action_recompute_all_data()
        self.write({'state': 'lock_normal'})

    def action_lock_ot(self):
        self.action_recompute_all_data()
        self.write({'state': 'lock_ot'})

    def action_lock_regime(self):
        self.action_recompute_all_data()
        self.write({'state': 'lock_regime'})

    def action_lock_kpi(self):
        self.action_recompute_all_data()
        self.write({'state': 'lock_kpi'})

    def action_confirm(self):
        self.action_recompute_all_data()
        self.write({'state': 'confirmed'})

    # Các hàm quay lại trạng thái trước
    def action_back_to_draft(self):
        """Khi quay lại dự thảo, xoá sạch mọi kết quả tính toán."""
        for rec in self:
            if rec.line_ids:
                rec.line_ids.action_reset_data()
            rec.write({'state': 'draft'})
        # Cập nhật lại thống kê tháng sau khi reset dòng con
        self._compute_quick_stats()

    def action_back_to_lock_normal(self):
        self.action_recompute_all_data()
        self.write({'state': 'lock_normal'})

    def action_back_to_lock_ot(self):
        # Xóa dữ liệu KPI khi quay lại trạng thái trước
        self.line_ids.write({
            'payroll_kpi_score': 0,
            'payroll_kpi_amount': 0,
            'payroll_cash_amount': 0,
            'kpi_c1_productivity': 0,
            'kpi_c2_discipline': 0,
            'kpi_c3_teamwork': 0,
            'kpi_c4_5s': 0,
            'kpi_c5_saving': 0,
        })
        self.action_recompute_all_data()
        self.write({'state': 'lock_ot'})

    def action_back_to_lock_regime(self):
        self.action_recompute_all_data()
        self.write({'state': 'lock_regime'})

    def action_back_to_lock_kpi(self):
        self.action_recompute_all_data()
        self.write({'state': 'lock_kpi'})

    def action_draft(self):
        # Giữ lại hàm này để tương thích nếu cần, hoặc xoá nếu muốn ép quy trình quay lại từng bước
        self.write({'state': 'draft'})

    def _action_init_overtime_suggestions(self):
        """Khởi tạo dữ liệu gợi ý công làm thêm dựa trên công thường (N -> 0.5N, Đ -> 0.5Đ)"""
        from datetime import date
        n_ot = self.env['dl.salary.kpi.attendance.type'].search([('code', '=', '0.5N')], limit=1)
        d_ot = self.env['dl.salary.kpi.attendance.type'].search([('code', '=', '0.5Đ')], limit=1)
        month_date = self.date_month
        year, month = month_date.year, month_date.month
        
        n_ot_id = n_ot.id if n_ot else False
        d_ot_id = d_ot.id if d_ot else False
        
        if not n_ot_id or not d_ot_id:
            return

        for line in self.line_ids:
            vals = {}
            for i in range(1, 32):
                ot_field = f'ot_day_{i:02d}'
                norm_field = f'day_{i:02d}'
                
                norm_att = getattr(line, norm_field)
                new_ot_value = False
                if norm_att and norm_att.code:
                    code = norm_att.code.strip().upper()
                    if code == 'N':
                        new_ot_value = n_ot_id
                    elif code == 'Đ':
                        new_ot_value = d_ot_id
                
                vals[ot_field] = new_ot_value
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

    def action_import_internal_salary(self):
        self.ensure_one()
        return {
            'name': 'Nhập Lương nội bộ (KPI Target)',
            'type': 'ir.actions.act_window',
            'res_model': 'dl.salary.kpi.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_month_id': self.id, 'default_wizard_type': 'internal_salary'}
        }

    def action_export_ot_excel(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/dl_salary_kpi/export_ot_attendance/{self.id}',
            'target': 'new',
        }

    def action_export_internal_salary_excel(self):
        """Xuất file mẫu nhập Lương nội bộ (Ln)"""
        self.ensure_one()
        import io
        import base64
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Alignment, Border, Side, Font, PatternFill
        except ImportError:
            raise UserError("Vui lòng cài đặt thư viện openpyxl!")

        wb = Workbook()
        ws = wb.active
        ws.title = "Bang Luong Noi Bo"

        # Định dạng
        thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        header_fill = PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")
        header_font = Font(bold=True)
        center_align = Alignment(horizontal='center', vertical='center')

        # Header dòng 3 (Theo chuẩn các file import khác)
        headers = ['STT', 'Số CCCD', 'Họ và Tên', 'Bộ phận', 'Số công', 'Thực lĩnh (Ln)']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.border = thin_border
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center_align

        # Dữ liệu từ dòng 4
        row_idx = 4
        stt = 1
        for line in self.line_ids:
            # A: STT
            ws.cell(row=row_idx, column=1, value=stt).border = thin_border
            # B: CCCD
            ws.cell(row=row_idx, column=2, value=line.identification_id or '').border = thin_border
            # C: Họ tên
            ws.cell(row=row_idx, column=3, value=line.employee_name or '').border = thin_border
            # D: Bộ phận
            ws.cell(row=row_idx, column=4, value=line.dl_tax_department_id.name or '').border = thin_border
            # E: Số công (Mặc định 0)
            ws.cell(row=row_idx, column=5, value=0).border = thin_border
            # F: Thực lĩnh (Mặc định 0) - Hoặc lấy payroll_internal_salary hiện tại
            ws.cell(row=row_idx, column=6, value=line.payroll_internal_salary or 0).border = thin_border
            
            row_idx += 1
            stt += 1

        # Căn chỉnh độ rộng cột
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 30
        ws.column_dimensions['D'].width = 25
        ws.column_dimensions['F'].width = 15

        output = io.BytesIO()
        wb.save(output)
        file_data = base64.b64encode(output.getvalue())
        output.close()

        filename = f"MAU_NHAP_LUONG_NOI_BO_{self.date_month.strftime('%m_%Y')}.xlsx"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': file_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_("Bạn không thể xóa phiếu cân đối bảng công khi không ở trạng thái Dự thảo!"))
        return super(SalaryKpiMonth, self).unlink()

    # --- LOGIC XUẤT BÁO CÁO LƯƠNG TRỰC TIẾP (KHÔNG POPUP) ---

    def _safe_write(self, ws, row, col, value):
        """Ghi dữ liệu an toàn vào ô, tránh ghi vào ô phụ của vùng gộp"""
        cell = ws.cell(row=row, column=col)
        if isinstance(cell, MergedCell):
            for merged_range in ws.merged_cells.ranges:
                if cell.coordinate in merged_range:
                    master_cell = ws.cell(row=merged_range.min_row, column=merged_range.min_col)
                    master_cell.value = value
                    return
        else:
            cell.value = value

    def _copy_row_formatting(self, ws, source_row, target_row):
        """Sao chép định dạng và dịch công thức từ dòng nguồn sang dòng đích một cách triệt để"""
        for col in range(1, ws.max_column + 1):
            source_cell = ws.cell(row=source_row, column=col)
            target_cell = ws.cell(row=target_row, column=col)

            # 1. Sao chép giá trị hoặc dịch công thức
            if source_cell.data_type == 'f':
                target_cell.value = Translator(source_cell.value, origin=source_cell.coordinate).translate_formula(target_cell.coordinate)
            else:
                target_cell.value = source_cell.value

            # 2. Sao chép toàn bộ định dạng (Styles)
            if source_cell.has_style:
                target_cell.font = copy.copy(source_cell.font)
                target_cell.border = copy.copy(source_cell.border)
                target_cell.fill = copy.copy(source_cell.fill)
                target_cell.number_format = source_cell.number_format  # Number format là string, gán trực tiếp
                target_cell.protection = copy.copy(source_cell.protection)
                target_cell.alignment = copy.copy(source_cell.alignment)
        
        # 3. Sao chép chiều cao dòng
        if ws.row_dimensions[source_row].height:
            ws.row_dimensions[target_row].height = ws.row_dimensions[source_row].height

    def action_export_salary_report(self):
        """Hàm xuất báo cáo lương trực tiếp theo Skill Template 01"""
        self.ensure_one()
        if not load_workbook:
            raise UserError(_("Thư viện openpyxl chưa được cài đặt."))

        try:
            template_path = file_path('dl_salary_kpi/static/src/templates/TEMPLATE_2026.xlsx')
        except FileNotFoundError:
            raise UserError(_("Không tìm thấy file mẫu Excel tại static/src/templates/TEMPLATE_2026.xlsx"))

        t0 = time.time()
        wb = load_workbook(template_path)
        wb.calculation.fullCalcOnLoad = True
        ws = wb.active
        month_date = self.date_month
        
        t1 = time.time()
        _logger.info("=== EXPORT LƯƠNG [%s]: Bước 1 - Tải Template mất %.2fs ===", self.name, t1 - t0)
        
        ws.title = f"Tháng {month_date.strftime('%m')} - năm {month_date.strftime('%Y')}"

        # 1. Header
        self._safe_write(ws, 3, 1, f"Tháng {month_date.strftime('%m')} năm {month_date.strftime('%Y')}")
        self._safe_write(ws, 4, 7, self.dl_revenue)
        self._safe_write(ws, 4, 12, int(month_date.strftime('%m')))
        self._safe_write(ws, 4, 16, int(month_date.strftime('%Y')))
        
        # Ghi tên khoản thưởng vào ô EC5 (Cột 133)
        bonus_names = [b.name for b in self.bonus_line_ids]
        if bonus_names:
            self._safe_write(ws, 5, 133, " + ".join(bonus_names))
        else:
            self._safe_write(ws, 5, 133, "")

        # 2. Data
        current_row = 8
        time_copy = 0.0
        time_map = 0.0
        
        for i, line in enumerate(self.line_ids):
            t_start_row = time.time()
            if current_row > 8:
                self._copy_row_formatting(ws, 8, current_row)
            
            t_after_copy = time.time()
            time_copy += (t_after_copy - t_start_row)
            
            # Mapping
            self._safe_write(ws, current_row, 1, i + 1)
            self._safe_write(ws, current_row, 2, line.employee_id.dl_tax_id or '')
            self._safe_write(ws, current_row, 3, line.employee_id.name)
            birthday_str = line.employee_id.birthday.strftime('%d/%m/%Y') if line.employee_id.birthday else ''
            self._safe_write(ws, current_row, 4, birthday_str)
            self._safe_write(ws, current_row, 5, line.employee_id.identification_id or '')
            gender = 'Nam' if line.employee_id.sex == 'male' else 'Nữ' if line.employee_id.sex == 'female' else ''
            self._safe_write(ws, current_row, 6, gender)
            self._safe_write(ws, current_row, 7, line.employee_id.dl_tax_department_id.name or '')
            self._safe_write(ws, current_row, 8, line.employee_id.dl_tax_position or '')
            self._safe_write(ws, current_row, 9, line.employee_id.dl_tax_base_salary or 0)

            from calendar import monthrange
            from datetime import date
            last_day = monthrange(month_date.year, month_date.month)[1]

            for day in range(1, 32):
                # 1. Ghi công thường (Vùng J -> AN | Cột 10 -> 40)
                col_idx = 9 + day
                att_type = getattr(line, f'day_{day:02d}')
                self._safe_write(ws, current_row, col_idx, att_type.code if att_type else '')
                
                # 2. Ghi công làm thêm (Vùng AT -> BX | Cột 46 -> 76)
                # Ghi mã công làm thêm hoặc ghi rỗng để xoá công thức của Template nếu trên Odoo không có dữ liệu
                if day <= last_day:
                    ot_att = getattr(line, f'ot_day_{day:02d}')
                    col_ot = 45 + day
                    self._safe_write(ws, current_row, col_ot, ot_att.code if ot_att else '')

            if line.employee_id.sex == 'female':
                self._safe_write(ws, current_row, 95, self.dl_women_allowance)
            else:
                self._safe_write(ws, current_row, 95, 0)
            
            self._safe_write(ws, current_row, 96, self.dl_meal_allowance)
            
            # DG (111) Lương KPI: Ghi số tiền KPI cân đối
            if line.payroll_kpi_amount:
                self._safe_write(ws, current_row, 111, line.payroll_kpi_amount)
            else:
                self._safe_write(ws, current_row, 111, 0)
            
            # EE (135) Thưởng cố định năm
            self._safe_write(ws, current_row, 135, line.payroll_annual_bonus or 0)

            # EH (138) Số người phụ thuộc
            self._safe_write(ws, current_row, 138, line.payroll_pit_number_of_dependents or 0)

            # DP (120) Thuế TNCN
            self._safe_write(ws, current_row, 120, line.payroll_deduction_tncn or 0)
            
            # EC (133) Thưởng lễ
            total_bonus = 0
            for bonus in self.bonus_line_ids:
                emp_sex = line.employee_id.sex
                if bonus.gender == 'all' or \
                   (bonus.gender == 'female' and emp_sex == 'female') or \
                   (bonus.gender == 'male' and emp_sex == 'male'):
                    total_bonus += bonus.amount
            self._safe_write(ws, current_row, 133, total_bonus)

            t_after_map = time.time()
            time_map += (t_after_map - t_after_copy)

            current_row += 1

        t2 = time.time()
        _logger.info("=== EXPORT LƯƠNG [%s]: Bước 2 - Đổ %d dòng dữ liệu mất %.2fs ===", self.name, len(self.line_ids), t2 - t1)
        _logger.info("    -> Thời gian Copy Format: %.2fs", time_copy)
        _logger.info("    -> Thời gian Map Dữ liệu: %.2fs", time_map)

        # 3. Export
        output = io.BytesIO()
        wb.save(output)
        file_data = base64.b64encode(output.getvalue())
        output.close()
        
        t3 = time.time()
        _logger.info("=== EXPORT LƯƠNG [%s]: Bước 3 - Lưu file Excel mất %.2fs ===", self.name, t3 - t2)
        _logger.info("=== EXPORT LƯƠNG [%s]: TỔNG THỜI GIAN MẤT %.2fs ===", self.name, t3 - t0)

        filename = f"BC_LUONG_KPI_{month_date.strftime('%m_%Y')}.xlsx"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': file_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

    def action_generate_all_kpi(self):
        """
        Kích hoạt tính toán KPI cho toàn bộ nhân viên trong tháng.
        - Mỗi nhân viên được gán điểm ngẫu nhiên trong khoảng cho phép.
        - Đảm bảo số người đạt điểm tối đa (70) không quá 50% tổng số nhân viên.
        """
        self.ensure_one()
        from odoo.exceptions import UserError
        if self.state in ['lock_kpi', 'confirmed']:
            raise UserError("Bảng lương đã chốt KPI hoặc đã xác nhận, không thể tính toán lại.")
            
        if not self.line_ids:
            return True
            
        import random
        
        # 1. Chuẩn bị danh sách nhân viên và quota
        lines = list(self.line_ids)
        random.shuffle(lines) # Shuffle để việc phân bổ quota 70 được ngẫu nhiên
        
        total_employees = len(lines)
        quota_70 = total_employees // 2 # Tối đa 50% số người được điểm 70
        count_70 = 0
        
        # 2. Xử lý từng nhân viên
        for line in lines:
            # Nếu chưa đạt quota 70, cho phép random tới 70
            if count_70 < quota_70:
                line.action_generate_kpi_scores(max_allowed=70)
                # Kiểm tra xem thực tế line này có được gán 70 không
                if line.payroll_kpi_score == 70:
                    count_70 += 1
            else:
                # Nếu đã hết quota, chỉ cho phép random tới tối đa 69
                line.action_generate_kpi_scores(max_allowed=69)
                
        return True

    def action_export_kpi_point_report(self):
        """Xuất báo cáo điểm KPI theo mẫu TEMPLATE_KPI_2026.xlsx, chia sheet theo phòng ban."""
        self.ensure_one()
        file_data, filename = kpi_export_logic.export_kpi_point_excel(self)
        
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': file_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
