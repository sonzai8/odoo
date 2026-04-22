# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SalaryKpiLine(models.Model):
    _name = 'dl.salary.kpi.line'
    _description = 'Dòng chấm công tháng'
    _order = 'dl_tax_department, dl_first_name'

    month_id = fields.Many2one('dl.salary.kpi.month', string='Tháng bảng công', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True)
    employee_name = fields.Char(related='employee_id.name', string='Tên nhân viên', store=True)
    dl_first_name = fields.Char(related='employee_id.dl_first_name', string='Tên riêng', store=True)
    identification_id = fields.Char(related='employee_id.identification_id', string='Số CCCD', store=True)
    
    dl_tax_department = fields.Char(related='employee_id.dl_tax_department', string='Phòng ban', store=True)
    dl_tax_position = fields.Char(related='employee_id.dl_tax_position', string='Chức vụ', store=True)


    # Chấm công 31 ngày (hiển thị mã công)
    day_01 = fields.Many2one('dl.salary.kpi.attendance.type', string='01')
    day_02 = fields.Many2one('dl.salary.kpi.attendance.type', string='02')
    day_03 = fields.Many2one('dl.salary.kpi.attendance.type', string='03')
    day_04 = fields.Many2one('dl.salary.kpi.attendance.type', string='04')
    day_05 = fields.Many2one('dl.salary.kpi.attendance.type', string='05')
    day_06 = fields.Many2one('dl.salary.kpi.attendance.type', string='06')
    day_07 = fields.Many2one('dl.salary.kpi.attendance.type', string='07')
    day_08 = fields.Many2one('dl.salary.kpi.attendance.type', string='08')
    day_09 = fields.Many2one('dl.salary.kpi.attendance.type', string='09')
    day_10 = fields.Many2one('dl.salary.kpi.attendance.type', string='10')
    day_11 = fields.Many2one('dl.salary.kpi.attendance.type', string='11')
    day_12 = fields.Many2one('dl.salary.kpi.attendance.type', string='12')
    day_13 = fields.Many2one('dl.salary.kpi.attendance.type', string='13')
    day_14 = fields.Many2one('dl.salary.kpi.attendance.type', string='14')
    day_15 = fields.Many2one('dl.salary.kpi.attendance.type', string='15')
    day_16 = fields.Many2one('dl.salary.kpi.attendance.type', string='16')
    day_17 = fields.Many2one('dl.salary.kpi.attendance.type', string='17')
    day_18 = fields.Many2one('dl.salary.kpi.attendance.type', string='18')
    day_19 = fields.Many2one('dl.salary.kpi.attendance.type', string='19')
    day_20 = fields.Many2one('dl.salary.kpi.attendance.type', string='20')
    day_21 = fields.Many2one('dl.salary.kpi.attendance.type', string='21')
    day_22 = fields.Many2one('dl.salary.kpi.attendance.type', string='22')
    day_23 = fields.Many2one('dl.salary.kpi.attendance.type', string='23')
    day_24 = fields.Many2one('dl.salary.kpi.attendance.type', string='24')
    day_25 = fields.Many2one('dl.salary.kpi.attendance.type', string='25')
    day_26 = fields.Many2one('dl.salary.kpi.attendance.type', string='26')
    day_27 = fields.Many2one('dl.salary.kpi.attendance.type', string='27')
    day_28 = fields.Many2one('dl.salary.kpi.attendance.type', string='28')
    day_29 = fields.Many2one('dl.salary.kpi.attendance.type', string='29')
    day_30 = fields.Many2one('dl.salary.kpi.attendance.type', string='30')
    day_31 = fields.Many2one('dl.salary.kpi.attendance.type', string='31')

    # Các trường ẩn để xác định Chủ Nhật (dùng cho decoration trên web)
    day_01_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_02_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_03_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_04_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_05_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_06_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_07_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_08_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_09_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_10_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_11_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_12_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_13_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_14_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_15_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_16_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_17_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_18_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_19_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_20_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_21_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_22_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_23_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_24_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_25_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_26_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_27_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_28_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_29_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_30_is_sunday = fields.Boolean(compute='_compute_is_sunday')
    day_31_is_sunday = fields.Boolean(compute='_compute_is_sunday')

    # Các trường liên kết để lấy mã công (dùng cho decoration trên web)
    day_01_code = fields.Char(related='day_01.code', store=True)
    day_02_code = fields.Char(related='day_02.code', store=True)
    day_03_code = fields.Char(related='day_03.code', store=True)
    day_04_code = fields.Char(related='day_04.code', store=True)
    day_05_code = fields.Char(related='day_05.code', store=True)
    day_06_code = fields.Char(related='day_06.code', store=True)
    day_07_code = fields.Char(related='day_07.code', store=True)
    day_08_code = fields.Char(related='day_08.code', store=True)
    day_09_code = fields.Char(related='day_09.code', store=True)
    day_10_code = fields.Char(related='day_10.code', store=True)
    day_11_code = fields.Char(related='day_11.code', store=True)
    day_12_code = fields.Char(related='day_12.code', store=True)
    day_13_code = fields.Char(related='day_13.code', store=True)
    day_14_code = fields.Char(related='day_14.code', store=True)
    day_15_code = fields.Char(related='day_15.code', store=True)
    day_16_code = fields.Char(related='day_16.code', store=True)
    day_17_code = fields.Char(related='day_17.code', store=True)
    day_18_code = fields.Char(related='day_18.code', store=True)
    day_19_code = fields.Char(related='day_19.code', store=True)
    day_20_code = fields.Char(related='day_20.code', store=True)
    day_21_code = fields.Char(related='day_21.code', store=True)
    day_22_code = fields.Char(related='day_22.code', store=True)
    day_23_code = fields.Char(related='day_23.code', store=True)
    day_24_code = fields.Char(related='day_24.code', store=True)
    day_25_code = fields.Char(related='day_25.code', store=True)
    day_26_code = fields.Char(related='day_26.code', store=True)
    day_27_code = fields.Char(related='day_27.code', store=True)
    day_28_code = fields.Char(related='day_28.code', store=True)
    day_29_code = fields.Char(related='day_29.code', store=True)
    day_30_code = fields.Char(related='day_30.code', store=True)
    day_31_code = fields.Char(related='day_31.code', store=True)

    def _compute_is_sunday(self):


        from datetime import date
        for rec in self:
            if not rec.month_id.date_month:
                for i in range(1, 32):
                    rec[f'day_{i:02d}_is_sunday'] = False
                continue
                
            year = rec.month_id.date_month.year
            month = rec.month_id.date_month.month
            for i in range(1, 32):
                try:
                    d = date(year, month, i)
                    rec[f'day_{i:02d}_is_sunday'] = (d.weekday() == 6)
                except ValueError:
                    rec[f'day_{i:02d}_is_sunday'] = False

    @api.constrains('day_01', 'day_02', 'day_03', 'day_04', 'day_05', 'day_06', 'day_07', 'day_08', 'day_09', 'day_10',

                    'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20',
                    'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31')
    def _check_shift_change(self):
        """
        Kiểm tra quy tắc đổi ca: Nếu đổi từ công N (Ngày) sang Đ (Đêm)
        thì bắt buộc phải có ít nhất 1 ngày nghỉ ĐC ở giữa.
        """
        for rec in self:
            for i in range(1, 31):
                current_day = getattr(rec, f'day_{i:02d}')
                next_day = getattr(rec, f'day_{i+1:02d}')
                
                if current_day and next_day:
                    if current_day.code == 'N' and next_day.code == 'Đ':
                        raise ValidationError(_(
                            "Nhân viên %s: Lỗi quy tắc đổi ca tại ngày %02d-%02d. "
                            "Khi chuyển từ ca Ngày (N) sang ca Đêm (Đ), bắt buộc phải có ngày Đổi ca (ĐC) ở giữa."
                        ) % (rec.employee_name, i, i+1))

