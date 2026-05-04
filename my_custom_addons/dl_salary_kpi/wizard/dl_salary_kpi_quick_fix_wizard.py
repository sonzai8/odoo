# -*- coding: utf-8 -*-
import random
from datetime import date
from calendar import monthrange
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class SalaryKpiQuickFixWizard(models.TransientModel):
    """
    Wizard "Sửa nhanh công" cho dữ liệu bất thường.
    Cho phép người dùng nhập số lượng công cần giảm (N, Đ, 0.5N, 0.5Đ)
    và hệ thống sẽ tự động xóa ngẫu nhiên các ngày hợp lệ.
    """
    _name = 'dl.salary.kpi.quick.fix.wizard'
    _description = 'Sửa nhanh công chấm công'

    line_id = fields.Many2one('dl.salary.kpi.line', string='Dòng công', required=True, ondelete='cascade')
    employee_name = fields.Char(related='line_id.employee_name', string='Nhân viên', readonly=True)
    identification_id = fields.Char(related='line_id.identification_id', string='Số CCCD', readonly=True)

    # Thông tin tham khảo
    current_lk = fields.Monetary(related='line_id.payroll_net_salary_base', string='Thực lĩnh cơ sở (Lk)', readonly=True, currency_field='currency_id')
    target_salary = fields.Monetary(related='line_id.payroll_internal_salary', string='Lương nội bộ (Ln)', readonly=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='line_id.currency_id')

    # Số lượng muốn giảm (người dùng nhập)
    reduce_n = fields.Integer(string='Giảm công N (Ngày)', default=0,
                              help="Xóa cả công thường N và công làm thêm 0.5N của ngày đó.")
    reduce_d = fields.Integer(string='Giảm công Đ (Đêm)', default=0,
                              help="Xóa cả công thường Đ và công làm thêm 0.5Đ của ngày đó.")
    reduce_ot_n = fields.Integer(string='Giảm 0.5N (giữ N)', default=0,
                                 help="Chỉ xóa công làm thêm 0.5N, giữ nguyên công thường N.")
    reduce_ot_d = fields.Integer(string='Giảm 0.5Đ (giữ Đ)', default=0,
                                 help="Chỉ xóa công làm thêm 0.5Đ, giữ nguyên công thường Đ.")

    # Số lượng tối đa có thể giảm (hiển thị tham khảo)
    max_n = fields.Integer(string='Tối đa N', compute='_compute_max_values', store=False)
    max_d = fields.Integer(string='Tối đa Đ', compute='_compute_max_values', store=False)
    max_ot_n = fields.Integer(string='Tối đa 0.5N', compute='_compute_max_values', store=False)
    max_ot_d = fields.Integer(string='Tối đa 0.5Đ', compute='_compute_max_values', store=False)

    # HTML hiển thị gợi ý
    suggestion_html = fields.Html(related='line_id.payroll_anomaly_suggestion', string='Gợi ý xử lý', readonly=True)

    def _get_protected_days(self):
        """
        Xác định tập hợp các ngày KHÔNG được phép sửa.
        Một ngày bị bảo vệ nếu:
        - Bản thân nó là ĐC.
        - Ngày trước nó (i-1) là ĐC.
        - Ngày sau nó (i+1) là ĐC.
        """
        line = self.line_id
        protected = set()
        month_date = line.month_id.date_month
        last_day = monthrange(month_date.year, month_date.month)[1]

        for i in range(1, last_day + 1):
            att = getattr(line, f'day_{i:02d}')
            if att and att.code == 'ĐC':
                protected.add(i)
                if i > 1:
                    protected.add(i - 1)
                if i < last_day:
                    protected.add(i + 1)

        return protected

    def _get_eligible_days(self, code, field_prefix='day'):
        """
        Tìm danh sách các ngày hợp lệ có mã công = `code` và không nằm trong tập bảo vệ.
        field_prefix: 'day' cho công thường, 'ot_day' cho công làm thêm.
        """
        line = self.line_id
        protected = self._get_protected_days()
        month_date = line.month_id.date_month
        last_day = monthrange(month_date.year, month_date.month)[1]

        eligible = []
        for i in range(1, last_day + 1):
            if i in protected:
                continue
            att = getattr(line, f'{field_prefix}_{i:02d}')
            if att and att.code == code:
                eligible.append(i)

        return eligible

    @api.depends('line_id')
    def _compute_max_values(self):
        """Tính số lượng ngày hợp lệ tối đa có thể xóa cho mỗi loại công."""
        for wiz in self:
            if not wiz.line_id:
                wiz.max_n = 0
                wiz.max_d = 0
                wiz.max_ot_n = 0
                wiz.max_ot_d = 0
                continue

            wiz.max_n = len(wiz._get_eligible_days('N', 'day'))
            wiz.max_d = len(wiz._get_eligible_days('Đ', 'day'))
            wiz.max_ot_n = len(wiz._get_eligible_days('0.5N', 'ot_day'))
            wiz.max_ot_d = len(wiz._get_eligible_days('0.5Đ', 'ot_day'))

    def action_apply_quick_fix(self):
        """
        Thực hiện xóa công theo thứ tự:
        1. Giảm N (xóa cả day + ot_day)
        2. Giảm Đ (xóa cả day + ot_day)
        3. Giảm 0.5N (chỉ xóa ot_day, giữ day)
        4. Giảm 0.5Đ (chỉ xóa ot_day, giữ day)
        """
        self.ensure_one()
        line = self.line_id

        # Validate: phải nhập ít nhất 1 giá trị > 0
        if self.reduce_n <= 0 and self.reduce_d <= 0 and self.reduce_ot_n <= 0 and self.reduce_ot_d <= 0:
            raise ValidationError(_("Vui lòng nhập ít nhất 1 số lượng công cần giảm!"))

        vals = {}
        removed_n_days = set()  # Theo dõi các ngày đã xóa N để loại khỏi pool 0.5N
        removed_d_days = set()  # Theo dõi các ngày đã xóa Đ để loại khỏi pool 0.5Đ

        # === BƯỚC 1: Giảm công N (xóa cả day_XX và ot_day_XX) ===
        if self.reduce_n > 0:
            eligible_n = self._get_eligible_days('N', 'day')
            if self.reduce_n > len(eligible_n):
                raise ValidationError(
                    _(f"Không đủ công N để giảm! Yêu cầu: {self.reduce_n}, Có thể: {len(eligible_n)}"))

            random.shuffle(eligible_n)
            days_to_remove_n = eligible_n[:self.reduce_n]
            for day in days_to_remove_n:
                vals[f'day_{day:02d}'] = False
                vals[f'ot_day_{day:02d}'] = False
                removed_n_days.add(day)

        # === BƯỚC 2: Giảm công Đ (xóa cả day_XX và ot_day_XX) ===
        if self.reduce_d > 0:
            eligible_d = self._get_eligible_days('Đ', 'day')
            if self.reduce_d > len(eligible_d):
                raise ValidationError(
                    _(f"Không đủ công Đ để giảm! Yêu cầu: {self.reduce_d}, Có thể: {len(eligible_d)}"))

            random.shuffle(eligible_d)
            days_to_remove_d = eligible_d[:self.reduce_d]
            for day in days_to_remove_d:
                vals[f'day_{day:02d}'] = False
                vals[f'ot_day_{day:02d}'] = False
                removed_d_days.add(day)

        # === BƯỚC 3: Giảm 0.5N (chỉ xóa ot_day, giữ day) ===
        if self.reduce_ot_n > 0:
            eligible_ot_n = self._get_eligible_days('0.5N', 'ot_day')
            # Loại bỏ những ngày đã bị xóa công N ở bước 1 (vì ot_day đã bị xóa rồi)
            eligible_ot_n = [d for d in eligible_ot_n if d not in removed_n_days]

            if self.reduce_ot_n > len(eligible_ot_n):
                raise ValidationError(
                    _(f"Không đủ công 0.5N để giảm! Yêu cầu: {self.reduce_ot_n}, "
                      f"Có thể: {len(eligible_ot_n)} (đã trừ {len(removed_n_days)} ngày vừa xóa N)"))

            random.shuffle(eligible_ot_n)
            days_to_remove_ot_n = eligible_ot_n[:self.reduce_ot_n]
            for day in days_to_remove_ot_n:
                vals[f'ot_day_{day:02d}'] = False

        # === BƯỚC 4: Giảm 0.5Đ (chỉ xóa ot_day, giữ day) ===
        if self.reduce_ot_d > 0:
            eligible_ot_d = self._get_eligible_days('0.5Đ', 'ot_day')
            # Loại bỏ những ngày đã bị xóa công Đ ở bước 2 (vì ot_day đã bị xóa rồi)
            eligible_ot_d = [d for d in eligible_ot_d if d not in removed_d_days]

            if self.reduce_ot_d > len(eligible_ot_d):
                raise ValidationError(
                    _(f"Không đủ công 0.5Đ để giảm! Yêu cầu: {self.reduce_ot_d}, "
                      f"Có thể: {len(eligible_ot_d)} (đã trừ {len(removed_d_days)} ngày vừa xóa Đ)"))

            random.shuffle(eligible_ot_d)
            days_to_remove_ot_d = eligible_ot_d[:self.reduce_ot_d]
            for day in days_to_remove_ot_d:
                vals[f'ot_day_{day:02d}'] = False

        # === GHI DỮ LIỆU ===
        if vals:
            _logger.info(
                "=== QUICK FIX [%s - %s]: Xóa %d trường: %s ===",
                line.employee_name, line.identification_id,
                len(vals), list(vals.keys())
            )
            line.write(vals)

        return {'type': 'ir.actions.act_window_close'}
