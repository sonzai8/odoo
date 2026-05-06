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

    def _get_protected_days(self):
        line = self.line_id
        protected = set()
        month_date = line.month_id.date_month
        last_day = monthrange(month_date.year, month_date.month)[1]

        for i in range(1, last_day + 1):
            att = getattr(line, f'day_{i:02d}')
            if att and getattr(att, 'code', False) == 'ĐC':
                protected.add(i)
                if i > 1:
                    protected.add(i - 1)
                if i < last_day:
                    protected.add(i + 1)
        return protected

    def _get_days_by_condition(self, condition_func):
        line = self.line_id
        month_date = line.month_id.date_month
        last_day = monthrange(month_date.year, month_date.month)[1]
        days = []
        for i in range(1, last_day + 1):
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
            protected = wiz._get_protected_days()
            wiz.current_n = len([i for i in range(1, 32) if getattr(line, f'day_{i:02d}', False) and getattr(line, f'day_{i:02d}').code == 'N' and i not in protected])
            wiz.current_d = len([i for i in range(1, 32) if getattr(line, f'day_{i:02d}', False) and getattr(line, f'day_{i:02d}').code == 'Đ' and i not in protected])
            wiz.current_ot_n = len([i for i in range(1, 32) if getattr(line, f'ot_day_{i:02d}', False) and getattr(line, f'ot_day_{i:02d}').code == '0.5N' and i not in protected])
            wiz.current_ot_d = len([i for i in range(1, 32) if getattr(line, f'ot_day_{i:02d}', False) and getattr(line, f'ot_day_{i:02d}').code == '0.5Đ' and i not in protected])

    def action_apply_quick_fix(self):
        self.ensure_one()
        line = self.line_id

        if self.change_n == 0 and self.change_d == 0 and self.change_ot_n == 0 and self.change_ot_d == 0:
            raise ValidationError(_("Vui lòng nhập số lượng công cần thay đổi (khác 0)!"))

        vals = {}
        protected = self._get_protected_days()
        
        year = line.month_id.date_month.year if line.month_id.date_month else datetime.date.today().year
        month = line.month_id.date_month.month if line.month_id.date_month else datetime.date.today().month
        last_day = monthrange(year, month)[1]

        def is_weekday(d):
            try:
                date_obj = datetime.date(year, month, d)
                return date_obj.weekday() < 6 # 0-5 is Mon-Sat
            except ValueError:
                return False

        # Load types
        att_type_n = self.env['dl.salary.kpi.attendance.type'].search([('code', '=', 'N')], limit=1)
        att_type_d = self.env['dl.salary.kpi.attendance.type'].search([('code', '=', 'Đ')], limit=1)
        att_type_05n = self.env['dl.salary.kpi.attendance.type'].search([('code', '=', '0.5N')], limit=1)
        att_type_05d = self.env['dl.salary.kpi.attendance.type'].search([('code', '=', '0.5Đ')], limit=1)

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
            eligible = [d for d in range(1, last_day + 1) if d not in protected and get_current_code('day', d) == 'N']
            if count > len(eligible):
                raise ValidationError(_(f"Không đủ công N để giảm! Yêu cầu: {count}, Có thể: {len(eligible)}"))
            random.shuffle(eligible)
            for d in eligible[:count]:
                vals[f'day_{d:02d}'] = False
                vals[f'ot_day_{d:02d}'] = False

        if self.change_d < 0:
            count = abs(self.change_d)
            eligible = [d for d in range(1, last_day + 1) if d not in protected and get_current_code('day', d) == 'Đ']
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
            eligible = [d for d in range(1, last_day + 1) if d not in protected and get_current_code('ot_day', d) == '0.5N' and d not in temp_removed_days]
            if count > len(eligible):
                raise ValidationError(_(f"Không đủ công 0.5N để giảm! Yêu cầu: {count}, Có thể: {len(eligible)}"))
            random.shuffle(eligible)
            for d in eligible[:count]:
                vals[f'ot_day_{d:02d}'] = False
                temp_removed_days.add(d)

        if self.change_ot_d < 0:
            count = abs(self.change_ot_d)
            eligible = [d for d in range(1, last_day + 1) if d not in protected and get_current_code('ot_day', d) == '0.5Đ' and d not in temp_removed_days]
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
            # Find empty days, not protected, must be weekday (Mon-Sat)
            eligible = [d for d in range(1, last_day + 1) if d not in protected and is_weekday(d) and not get_simulated_code('day', d)]
            if count > len(eligible):
                raise ValidationError(_(f"Không đủ ngày trống từ T2-T7 để thêm {count} công N! Có thể thêm: {len(eligible)}"))
            random.shuffle(eligible)
            for d in eligible[:count]:
                vals[f'day_{d:02d}'] = att_type_n.id

        if self.change_d > 0:
            count = self.change_d
            eligible = [d for d in range(1, last_day + 1) if d not in protected and is_weekday(d) and not get_simulated_code('day', d)]
            if count > len(eligible):
                raise ValidationError(_(f"Không đủ ngày trống từ T2-T7 để thêm {count} công Đ! Có thể thêm: {len(eligible)}"))
            random.shuffle(eligible)
            for d in eligible[:count]:
                vals[f'day_{d:02d}'] = att_type_d.id

        if self.change_ot_n > 0:
            count = self.change_ot_n
            # Find days that have N (simulated), but no OT (simulated), not protected
            eligible = [d for d in range(1, last_day + 1) if d not in protected and get_simulated_code('day', d) == 'N' and not get_simulated_code('ot_day', d)]
            if count > len(eligible):
                raise ValidationError(_(f"Không đủ ngày N (đang trống OT) để thêm {count} công 0.5N! Có thể thêm: {len(eligible)}"))
            random.shuffle(eligible)
            for d in eligible[:count]:
                vals[f'ot_day_{d:02d}'] = att_type_05n.id

        if self.change_ot_d > 0:
            count = self.change_ot_d
            eligible = [d for d in range(1, last_day + 1) if d not in protected and get_simulated_code('day', d) == 'Đ' and not get_simulated_code('ot_day', d)]
            if count > len(eligible):
                raise ValidationError(_(f"Không đủ ngày Đ (đang trống OT) để thêm {count} công 0.5Đ! Có thể thêm: {len(eligible)}"))
            random.shuffle(eligible)
            for d in eligible[:count]:
                vals[f'ot_day_{d:02d}'] = att_type_05d.id

        # === GHI DỮ LIỆU ===
        if vals:
            _logger.info(
                "=== QUICK FIX [%s - %s]: Cập nhật %d trường: %s ===",
                line.employee_name, line.identification_id,
                len(vals), list(vals.keys())
            )
            line.write(vals)

        return {'type': 'ir.actions.act_window_close'}
