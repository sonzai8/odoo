# -*- coding: utf-8 -*-
import random
import datetime
from calendar import monthrange
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class SalaryKpiQuickFixWizard(models.TransientModel):
    """
    Wizard "Điều chỉnh công" cho dữ liệu bất thường.
    Cho phép người dùng nhập số lượng công cần thay đổi (Dương = Thêm, Âm = Giảm).
    """
    _name = 'dl.salary.kpi.quick.fix.wizard'
    _description = 'Điều chỉnh nhanh công chấm công'

    line_id = fields.Many2one('dl.salary.kpi.line', string='Dòng công', required=True, ondelete='cascade')
    employee_name = fields.Char(related='line_id.employee_name', string='Nhân viên', readonly=True)
    identification_id = fields.Char(related='line_id.identification_id', string='Số CCCD', readonly=True)

    # Thông tin tham khảo
    current_lk = fields.Monetary(related='line_id.payroll_net_salary_base', string='Thực lĩnh ngoài(TLN)', readonly=True, currency_field='currency_id')
    target_salary = fields.Monetary(related='line_id.payroll_internal_salary', string='Lương Nội Bộ (LNB)', readonly=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='line_id.currency_id')

    # Kết quả thực tế sau điều chỉnh
    payroll_kpi_score = fields.Float(related='line_id.payroll_kpi_score', string='Điểm KPI thực tế', readonly=True)
    payroll_kpi_amount_rounded = fields.Monetary(related='line_id.payroll_kpi_amount_rounded', string='Tiền KPI thực tế', readonly=True, currency_field='currency_id')
    payroll_bank_transfer_amount_rounded = fields.Monetary(related='line_id.payroll_bank_transfer_amount_rounded', string='Tiền CK thực tế', readonly=True, currency_field='currency_id')
    payroll_cash_amount_rounded = fields.Monetary(related='line_id.payroll_cash_amount_rounded', string='Tiền mặt thực tế', readonly=True, currency_field='currency_id')
    company_id = fields.Many2one('res.company', related='line_id.company_id', readonly=True)

    # Số lượng muốn thay đổi (người dùng nhập)
    change_n = fields.Integer(string='Thay đổi công N', default=0,
                              help="Nhập số dương để THÊM, số âm để GIẢM.")
    change_d = fields.Integer(string='Thay đổi công Đ', default=0,
                              help="Nhập số dương để THÊM, số âm để GIẢM.")
    change_ot_n = fields.Integer(string='Thay đổi 0.5N', default=0,
                                 help="Nhập số dương để THÊM, số âm để GIẢM.")
    change_ot_d = fields.Integer(string='Thay đổi 0.5Đ', default=0,
                                 help="Nhập số dương để THÊM, số âm để GIẢM.")

    # Thông tin Max (Hiện tại)
    current_n = fields.Integer(string='Công N hiện tại', compute='_compute_current_values', store=False)
    current_d = fields.Integer(string='Công Đ hiện tại', compute='_compute_current_values', store=False)
    current_ot_n = fields.Integer(string='0.5N hiện tại', compute='_compute_current_values', store=False)
    current_ot_d = fields.Integer(string='0.5Đ hiện tại', compute='_compute_current_values', store=False)

    suggestion_html = fields.Html(related='line_id.payroll_anomaly_suggestion', string='Gợi ý xử lý', readonly=True)

    # --- MA TRẬN CHẤM CÔNG TRONG POPUP ---
    # Công thường
    day_01 = fields.Many2one('dl.salary.kpi.attendance.type', string='01', domain="[('company_id', '=', company_id)]")
    day_02 = fields.Many2one('dl.salary.kpi.attendance.type', string='02', domain="[('company_id', '=', company_id)]")
    day_03 = fields.Many2one('dl.salary.kpi.attendance.type', string='03', domain="[('company_id', '=', company_id)]")
    day_04 = fields.Many2one('dl.salary.kpi.attendance.type', string='04', domain="[('company_id', '=', company_id)]")
    day_05 = fields.Many2one('dl.salary.kpi.attendance.type', string='05', domain="[('company_id', '=', company_id)]")
    day_06 = fields.Many2one('dl.salary.kpi.attendance.type', string='06', domain="[('company_id', '=', company_id)]")
    day_07 = fields.Many2one('dl.salary.kpi.attendance.type', string='07', domain="[('company_id', '=', company_id)]")
    day_08 = fields.Many2one('dl.salary.kpi.attendance.type', string='08', domain="[('company_id', '=', company_id)]")
    day_09 = fields.Many2one('dl.salary.kpi.attendance.type', string='09', domain="[('company_id', '=', company_id)]")
    day_10 = fields.Many2one('dl.salary.kpi.attendance.type', string='10', domain="[('company_id', '=', company_id)]")
    day_11 = fields.Many2one('dl.salary.kpi.attendance.type', string='11', domain="[('company_id', '=', company_id)]")
    day_12 = fields.Many2one('dl.salary.kpi.attendance.type', string='12', domain="[('company_id', '=', company_id)]")
    day_13 = fields.Many2one('dl.salary.kpi.attendance.type', string='13', domain="[('company_id', '=', company_id)]")
    day_14 = fields.Many2one('dl.salary.kpi.attendance.type', string='14', domain="[('company_id', '=', company_id)]")
    day_15 = fields.Many2one('dl.salary.kpi.attendance.type', string='15', domain="[('company_id', '=', company_id)]")
    day_16 = fields.Many2one('dl.salary.kpi.attendance.type', string='16', domain="[('company_id', '=', company_id)]")
    day_17 = fields.Many2one('dl.salary.kpi.attendance.type', string='17', domain="[('company_id', '=', company_id)]")
    day_18 = fields.Many2one('dl.salary.kpi.attendance.type', string='18', domain="[('company_id', '=', company_id)]")
    day_19 = fields.Many2one('dl.salary.kpi.attendance.type', string='19', domain="[('company_id', '=', company_id)]")
    day_20 = fields.Many2one('dl.salary.kpi.attendance.type', string='20', domain="[('company_id', '=', company_id)]")
    day_21 = fields.Many2one('dl.salary.kpi.attendance.type', string='21', domain="[('company_id', '=', company_id)]")
    day_22 = fields.Many2one('dl.salary.kpi.attendance.type', string='22', domain="[('company_id', '=', company_id)]")
    day_23 = fields.Many2one('dl.salary.kpi.attendance.type', string='23', domain="[('company_id', '=', company_id)]")
    day_24 = fields.Many2one('dl.salary.kpi.attendance.type', string='24', domain="[('company_id', '=', company_id)]")
    day_25 = fields.Many2one('dl.salary.kpi.attendance.type', string='25', domain="[('company_id', '=', company_id)]")
    day_26 = fields.Many2one('dl.salary.kpi.attendance.type', string='26', domain="[('company_id', '=', company_id)]")
    day_27 = fields.Many2one('dl.salary.kpi.attendance.type', string='27', domain="[('company_id', '=', company_id)]")
    day_28 = fields.Many2one('dl.salary.kpi.attendance.type', string='28', domain="[('company_id', '=', company_id)]")
    day_29 = fields.Many2one('dl.salary.kpi.attendance.type', string='29', domain="[('company_id', '=', company_id)]")
    day_30 = fields.Many2one('dl.salary.kpi.attendance.type', string='30', domain="[('company_id', '=', company_id)]")
    day_31 = fields.Many2one('dl.salary.kpi.attendance.type', string='31', domain="[('company_id', '=', company_id)]")

    # Làm thêm
    ot_day_01 = fields.Many2one('dl.salary.kpi.attendance.type', string='01 ', domain="[('company_id', '=', company_id)]")
    ot_day_02 = fields.Many2one('dl.salary.kpi.attendance.type', string='02 ', domain="[('company_id', '=', company_id)]")
    ot_day_03 = fields.Many2one('dl.salary.kpi.attendance.type', string='03 ', domain="[('company_id', '=', company_id)]")
    ot_day_04 = fields.Many2one('dl.salary.kpi.attendance.type', string='04 ', domain="[('company_id', '=', company_id)]")
    ot_day_05 = fields.Many2one('dl.salary.kpi.attendance.type', string='05 ', domain="[('company_id', '=', company_id)]")
    ot_day_06 = fields.Many2one('dl.salary.kpi.attendance.type', string='06 ', domain="[('company_id', '=', company_id)]")
    ot_day_07 = fields.Many2one('dl.salary.kpi.attendance.type', string='07 ', domain="[('company_id', '=', company_id)]")
    ot_day_08 = fields.Many2one('dl.salary.kpi.attendance.type', string='08 ', domain="[('company_id', '=', company_id)]")
    ot_day_09 = fields.Many2one('dl.salary.kpi.attendance.type', string='09 ', domain="[('company_id', '=', company_id)]")
    ot_day_10 = fields.Many2one('dl.salary.kpi.attendance.type', string='10 ', domain="[('company_id', '=', company_id)]")
    ot_day_11 = fields.Many2one('dl.salary.kpi.attendance.type', string='11 ', domain="[('company_id', '=', company_id)]")
    ot_day_12 = fields.Many2one('dl.salary.kpi.attendance.type', string='12 ', domain="[('company_id', '=', company_id)]")
    ot_day_13 = fields.Many2one('dl.salary.kpi.attendance.type', string='13 ', domain="[('company_id', '=', company_id)]")
    ot_day_14 = fields.Many2one('dl.salary.kpi.attendance.type', string='14 ', domain="[('company_id', '=', company_id)]")
    ot_day_15 = fields.Many2one('dl.salary.kpi.attendance.type', string='15 ', domain="[('company_id', '=', company_id)]")
    ot_day_16 = fields.Many2one('dl.salary.kpi.attendance.type', string='16 ', domain="[('company_id', '=', company_id)]")
    ot_day_17 = fields.Many2one('dl.salary.kpi.attendance.type', string='17 ', domain="[('company_id', '=', company_id)]")
    ot_day_18 = fields.Many2one('dl.salary.kpi.attendance.type', string='18 ', domain="[('company_id', '=', company_id)]")
    ot_day_19 = fields.Many2one('dl.salary.kpi.attendance.type', string='19 ', domain="[('company_id', '=', company_id)]")
    ot_day_20 = fields.Many2one('dl.salary.kpi.attendance.type', string='20 ', domain="[('company_id', '=', company_id)]")
    ot_day_21 = fields.Many2one('dl.salary.kpi.attendance.type', string='21 ', domain="[('company_id', '=', company_id)]")
    ot_day_22 = fields.Many2one('dl.salary.kpi.attendance.type', string='22 ', domain="[('company_id', '=', company_id)]")
    ot_day_23 = fields.Many2one('dl.salary.kpi.attendance.type', string='23 ', domain="[('company_id', '=', company_id)]")
    ot_day_24 = fields.Many2one('dl.salary.kpi.attendance.type', string='24 ', domain="[('company_id', '=', company_id)]")
    ot_day_25 = fields.Many2one('dl.salary.kpi.attendance.type', string='25 ', domain="[('company_id', '=', company_id)]")
    ot_day_26 = fields.Many2one('dl.salary.kpi.attendance.type', string='26 ', domain="[('company_id', '=', company_id)]")
    ot_day_27 = fields.Many2one('dl.salary.kpi.attendance.type', string='27 ', domain="[('company_id', '=', company_id)]")
    ot_day_28 = fields.Many2one('dl.salary.kpi.attendance.type', string='28 ', domain="[('company_id', '=', company_id)]")
    ot_day_29 = fields.Many2one('dl.salary.kpi.attendance.type', string='29 ', domain="[('company_id', '=', company_id)]")
    ot_day_30 = fields.Many2one('dl.salary.kpi.attendance.type', string='30 ', domain="[('company_id', '=', company_id)]")
    ot_day_31 = fields.Many2one('dl.salary.kpi.attendance.type', string='31 ', domain="[('company_id', '=', company_id)]")

    @api.model
    def default_get(self, fields_list):
        res = super(SalaryKpiQuickFixWizard, self).default_get(fields_list)
        line_id = self.env.context.get('active_id') or res.get('line_id')
        if line_id:
            line = self.env['dl.salary.kpi.line'].browse(line_id)
            for i in range(1, 32):
                res[f'day_{i:02d}'] = getattr(line, f'day_{i:02d}').id if getattr(line, f'day_{i:02d}') else False
                res[f'ot_day_{i:02d}'] = getattr(line, f'ot_day_{i:02d}').id if getattr(line, f'ot_day_{i:02d}') else False
        return res

    def _get_work_boundaries(self):
        """Trả về (first_day, last_day) là index của ngày có công đầu tiên và cuối cùng."""
        line = self.line_id
        first_day = 0
        last_day = 0
        for i in range(1, 32):
            if getattr(line, f'day_{i:02d}', False):
                if first_day == 0:
                    first_day = i
                last_day = i
        return first_day, last_day

    def _get_protected_days(self, check_boundaries=True):
        """
        Lấy danh sách các ngày không được phép XÓA công.
        check_boundaries=True: Bảo vệ cả ngày đầu và ngày cuối đi làm.
        """
        line = self.line_id
        protected = set()
        month_date = line.month_id.date_month
        last_day_in_month = monthrange(month_date.year, month_date.month)[1]

        # 1. Bảo vệ các ngày quanh ĐC (Đổi công)
        for i in range(1, last_day_in_month + 1):
            att = getattr(line, f'day_{i:02d}')
            if att and getattr(att, 'code', False) == 'ĐC':
                protected.add(i)
                if i > 1:
                    protected.add(i - 1)
                if i < last_day_in_month:
                    protected.add(i + 1)
        
        # 2. Bảo vệ ngày đầu tiên và cuối cùng đi làm (theo yêu cầu mới)
        if check_boundaries:
            first, last = self._get_work_boundaries()
            if first:
                protected.add(first)
            if last:
                protected.add(last)
                
        return protected

    def _get_days_by_condition(self, condition_func):
        line = self.line_id
        month_date = line.month_id.date_month
        last_day_in_month = monthrange(month_date.year, month_date.month)[1]
        days = []
        for i in range(1, last_day_in_month + 1):
            if condition_func(i):
                days.append(i)
        return days

    @api.depends('line_id')
    def _compute_current_values(self):
        for wiz in self:
            if not wiz.line_id:
                wiz.current_n = 0
                wiz.current_d = 0
                wiz.current_ot_n = 0
                wiz.current_ot_d = 0
                continue
                
            line = wiz.line_id
            protected = wiz._get_protected_days(check_boundaries=True)
            wiz.current_n = len([i for i in range(1, 32) if getattr(line, f'day_{i:02d}', False) and getattr(line, f'day_{i:02d}').code == 'N' and i not in protected])
            wiz.current_d = len([i for i in range(1, 32) if getattr(line, f'day_{i:02d}', False) and getattr(line, f'day_{i:02d}').code == 'Đ' and i not in protected])
            wiz.current_ot_n = len([i for i in range(1, 32) if getattr(line, f'ot_day_{i:02d}', False) and getattr(line, f'ot_day_{i:02d}').code == '0.5N' and i not in protected])
            wiz.current_ot_d = len([i for i in range(1, 32) if getattr(line, f'ot_day_{i:02d}', False) and getattr(line, f'ot_day_{i:02d}').code == '0.5Đ' and i not in protected])

    def action_apply_quick_fix(self):
        self.ensure_one()
        line = self.line_id

        # Chỉ kiểm tra nếu KHÔNG có thay đổi nào trong ma trận (so với ban đầu)
        # Để đơn giản, ta cứ cho phép bấm Xác nhận nếu người dùng muốn "Lưu ma trận"
        # Ta chỉ chặn nếu cả 4 ô nhập số đều là 0 VÀ không có tham số 'from_magic'
        
        # vals chứa các thay đổi từ 4 ô nhập số lượng
        vals = {}
        protected = self._get_protected_days(check_boundaries=True)
        first_boundary, last_boundary = self._get_work_boundaries()
        
        year = line.month_id.date_month.year if line.month_id.date_month else datetime.date.today().year
        month = line.month_id.date_month.month if line.month_id.date_month else datetime.date.today().month
        last_day_in_month = monthrange(year, month)[1]

        def is_weekday(d):
            try:
                date_obj = datetime.date(year, month, d)
                return date_obj.weekday() < 6 # 0-5 is Mon-Sat
            except ValueError:
                return False

        # Load types theo đúng công ty
        company_id = line.company_id.id
        att_type_n = self.env['dl.salary.kpi.attendance.type'].search([('code', '=', 'N'), ('company_id', '=', company_id)], limit=1)
        att_type_d = self.env['dl.salary.kpi.attendance.type'].search([('code', '=', 'Đ'), ('company_id', '=', company_id)], limit=1)
        att_type_05n = self.env['dl.salary.kpi.attendance.type'].search([('code', '=', '0.5N'), ('company_id', '=', company_id)], limit=1)
        att_type_05d = self.env['dl.salary.kpi.attendance.type'].search([('code', '=', '0.5Đ'), ('company_id', '=', company_id)], limit=1)

        # VALIDATION: Total N + D <= 27
        total_n = line.total_n + self.change_n
        total_d = line.total_d + self.change_d
        if total_n + total_d > 27:
            raise ValidationError(_("Tổng số công thường (N + Đ) sau khi thêm không được vượt quá 27 ngày!"))

        def get_current_code(field_prefix, day):
            val = getattr(line, f'{field_prefix}_{day:02d}', False)
            if val:
                return getattr(val, 'code', False)
            return False

        # --- XỬ LÝ SỐ ÂM (GIẢM CÔNG) ---
        if self.change_n < 0:
            count = abs(self.change_n)
            eligible = [d for d in range(1, last_day_in_month + 1) if d not in protected and get_current_code('day', d) == 'N']
            if count > len(eligible):
                raise ValidationError(_(f"Không đủ công N để giảm! Yêu cầu: {count}, Có thể: {len(eligible)}"))
            random.shuffle(eligible)
            for d in eligible[:count]:
                vals[f'day_{d:02d}'] = False
                vals[f'ot_day_{d:02d}'] = False

        if self.change_d < 0:
            count = abs(self.change_d)
            eligible = [d for d in range(1, last_day_in_month + 1) if d not in protected and get_current_code('day', d) == 'Đ']
            if count > len(eligible):
                raise ValidationError(_(f"Không đủ công Đ để giảm! Yêu cầu: {count}, Có thể: {len(eligible)}"))
            random.shuffle(eligible)
            for d in eligible[:count]:
                vals[f'day_{d:02d}'] = False
                vals[f'ot_day_{d:02d}'] = False

        # Apply removals temporarily to not mess up pool for OT removal
        temp_removed_days = set()
        for k, v in vals.items():
            if not v:
                day_num = int(k.split('_')[-1])
                temp_removed_days.add(day_num)

        if self.change_ot_n < 0:
            count = abs(self.change_ot_n)
            eligible = [d for d in range(1, last_day_in_month + 1) if d not in protected and get_current_code('ot_day', d) == '0.5N' and d not in temp_removed_days]
            if count > len(eligible):
                raise ValidationError(_(f"Không đủ công 0.5N để giảm! Yêu cầu: {count}, Có thể: {len(eligible)}"))
            random.shuffle(eligible)
            for d in eligible[:count]:
                vals[f'ot_day_{d:02d}'] = False
                temp_removed_days.add(d)

        if self.change_ot_d < 0:
            count = abs(self.change_ot_d)
            eligible = [d for d in range(1, last_day_in_month + 1) if d not in protected and get_current_code('ot_day', d) == '0.5Đ' and d not in temp_removed_days]
            if count > len(eligible):
                raise ValidationError(_(f"Không đủ công 0.5Đ để giảm! Yêu cầu: {count}, Có thể: {len(eligible)}"))
            random.shuffle(eligible)
            for d in eligible[:count]:
                vals[f'ot_day_{d:02d}'] = False
                temp_removed_days.add(d)

        # --- XỬ LÝ SỐ DƯƠNG (THÊM CÔNG) ---
        # Helper to simulate current state considering `vals` overrides
        def get_simulated_code(field_prefix, day):
            key = f'{field_prefix}_{day:02d}'
            if key in vals:
                val = vals[key]
                if val is False:
                    return False
                return self.env['dl.salary.kpi.attendance.type'].browse(val).code
            return get_current_code(field_prefix, day)

        if self.change_n > 0:
            count = self.change_n
            # Chỉ thêm vào các ngày TRONG KHOẢNG [first_boundary, last_boundary]
            eligible = [d for d in range(1, last_day_in_month + 1) 
                        if d not in protected and is_weekday(d) and not get_simulated_code('day', d)
                        and first_boundary <= d <= last_boundary]
            
            if count > len(eligible):
                msg = _(f"Không đủ ngày trống từ T2-T7 trong khoảng làm việc ({first_boundary}->{last_boundary}) để thêm {count} công N! Có thể thêm: {len(eligible)}")
                if not first_boundary:
                    msg = _("Không thể thêm công vì nhân viên chưa có bất kỳ ngày công nào để xác định khoảng làm việc!")
                raise ValidationError(msg)
            random.shuffle(eligible)
            for d in eligible[:count]:
                vals[f'day_{d:02d}'] = att_type_n.id

        if self.change_d > 0:
            count = self.change_d
            eligible = [d for d in range(1, last_day_in_month + 1) 
                        if d not in protected and is_weekday(d) and not get_simulated_code('day', d)
                        and first_boundary <= d <= last_boundary]
            
            if count > len(eligible):
                msg = _(f"Không đủ ngày trống từ T2-T7 trong khoảng làm việc ({first_boundary}->{last_boundary}) để thêm {count} công Đ! Có thể thêm: {len(eligible)}")
                if not first_boundary:
                    msg = _("Không thể thêm công vì nhân viên chưa có bất kỳ ngày công nào để xác định khoảng làm việc!")
                raise ValidationError(msg)
            random.shuffle(eligible)
            for d in eligible[:count]:
                vals[f'day_{d:02d}'] = att_type_d.id

        if self.change_ot_n > 0:
            count = self.change_ot_n
            # Find days that have N (simulated), but no OT (simulated), not protected
            eligible = [d for d in range(1, last_day_in_month + 1) 
                        if d not in protected and get_simulated_code('day', d) == 'N' and not get_simulated_code('ot_day', d)
                        and first_boundary <= d <= last_boundary]
            
            if count > len(eligible):
                raise ValidationError(_(f"Không đủ ngày N (đang trống OT) trong khoảng làm việc để thêm {count} công 0.5N! Có thể thêm: {len(eligible)}"))
            random.shuffle(eligible)
            for d in eligible[:count]:
                vals[f'ot_day_{d:02d}'] = att_type_05n.id

        if self.change_ot_d > 0:
            count = self.change_ot_d
            eligible = [d for d in range(1, last_day_in_month + 1) 
                        if d not in protected and get_simulated_code('day', d) == 'Đ' and not get_simulated_code('ot_day', d)
                        and first_boundary <= d <= last_boundary]
            
            if count > len(eligible):
                raise ValidationError(_(f"Không đủ ngày Đ (đang trống OT) trong khoảng làm việc để thêm {count} công 0.5Đ! Có thể thêm: {len(eligible)}"))
            random.shuffle(eligible)
            for d in eligible[:count]:
                vals[f'ot_day_{d:02d}'] = att_type_05d.id

        # 1. Tính toán các thay đổi từ ô nhập số lượng (vals)
        # (Giữ nguyên logic random tìm ngày để thêm/giảm như cũ)
        # ... logic này đã chạy và tạo ra dict `vals` ...
        
        # 2. Lấy dữ liệu HIỆN TẠI trên ma trận của Wizard (người dùng có thể đã sửa tay)
        wizard_matrix_vals = {}
        for i in range(1, 32):
            f_day = f'day_{i:02d}'
            f_ot = f'ot_day_{i:02d}'
            wizard_matrix_vals[f_day] = self[f_day].id if self[f_day] else False
            wizard_matrix_vals[f_ot] = self[f_ot].id if self[f_ot] else False
            
        # 3. Ghi đè các thay đổi từ "Điều chỉnh nhanh" (vals) vào ma trận của Wizard
        # Điều này giúp hợp nhất cả sửa tay và sửa tự động
        for k, v in vals.items():
            wizard_matrix_vals[k] = v

        if wizard_matrix_vals:
            _logger.info("=== LƯU THAY ĐỔI CHO %s ===", line.employee_name)
            line.write(wizard_matrix_vals)
            
            # Tính lại kết quả
            line.action_generate_kpi_scores(max_allowed=70)
            
            # Reset ô nhập số
            self.write({
                'change_n': 0, 'change_d': 0, 'change_ot_n': 0, 'change_ot_d': 0,
            })
            
            # Cập nhật lại các trường ma trận trên chính Wizard để đồng bộ hiển thị
            self.write(wizard_matrix_vals)

        # KHÔNG ĐÓNG POPUP, MỞ LẠI CHÍNH MÌNH ĐỂ XEM KẾT QUẢ THỰC TẾ
        return {
            'type': 'ir.actions.act_window',
            'name': _('Điều chỉnh công nhanh'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'size': 'extra-large',
            'context': self.env.context,
        }

    def action_wing_magic(self):
        """
        PHÉP THUẬT WING: Gọi logic dùng chung từ Model.
        """
        self.ensure_one()
        self.line_id.action_run_wing_magic_logic()
        
        # Cập nhật lại ma trận trên Wizard để đồng bộ hiển thị
        for i in range(1, 32):
            self[f'day_{i:02d}'] = getattr(self.line_id, f'day_{i:02d}').id if getattr(self.line_id, f'day_{i:02d}') else False
            self[f'ot_day_{i:02d}'] = getattr(self.line_id, f'ot_day_{i:02d}').id if getattr(self.line_id, f'ot_day_{i:02d}') else False

        return {
            'type': 'ir.actions.act_window',
            'name': _('Điều chỉnh công nhanh'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'size': 'extra-large',
            'context': self.env.context,
        }

        # Cập nhật lại wizard sau phép thuật
        return {
            'type': 'ir.actions.act_window',
            'name': _('Điều chỉnh công nhanh'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'size': 'extra-large',
            'context': self.env.context,
        }
    # --- LIVE EDIT CHO MA TRẬN ---
    @api.onchange('day_01', 'day_02', 'day_03', 'day_04', 'day_05', 'day_06', 'day_07', 'day_08', 'day_09', 'day_10',
                  'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20',
                  'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31',
                  'ot_day_01', 'ot_day_02', 'ot_day_03', 'ot_day_04', 'ot_day_05', 'ot_day_06', 'ot_day_07', 'ot_day_08', 'ot_day_09', 'ot_day_10',
                  'ot_day_11', 'ot_day_12', 'ot_day_13', 'ot_day_14', 'ot_day_15', 'ot_day_16', 'ot_day_17', 'ot_day_18', 'ot_day_19', 'ot_day_20',
                  'ot_day_21', 'ot_day_22', 'ot_day_23', 'ot_day_24', 'ot_day_25', 'ot_day_26', 'ot_day_27', 'ot_day_28', 'ot_day_29', 'ot_day_30', 'ot_day_31')
    def _onchange_matrix_live_edit(self):
        """Khi thay đổi trên ma trận, ghi ngay vào line_id."""
        if not self.line_id:
            return
        vals = {}
        # Lấy tên field vừa thay đổi (Odoo không cho biết trực tiếp field nào trigger onchange dễ dàng ở đây)
        # nên ta cứ loop qua hết và so sánh hoặc ghi đè toàn bộ.
        for i in range(1, 32):
            f_day = f'day_{i:02d}'
            f_ot = f'ot_day_{i:02d}'
            vals[f_day] = self[f_day].id if self[f_day] else False
            vals[f_ot] = self[f_ot].id if self[f_ot] else False
        
        self.line_id.write(vals)
        # Tạm thời không gọi recalculate ở onchange để tránh lag, 
        # người dùng bấm nút Wing hoặc popup sẽ tự refresh khi mở lại.
        # Hoặc gọi nhẹ:
        self.line_id.action_generate_kpi_scores(max_allowed=70)
