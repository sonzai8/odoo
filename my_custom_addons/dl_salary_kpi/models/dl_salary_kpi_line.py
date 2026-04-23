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
    day_01 = fields.Many2one('dl.salary.kpi.attendance.type', string='01', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_02 = fields.Many2one('dl.salary.kpi.attendance.type', string='02', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_03 = fields.Many2one('dl.salary.kpi.attendance.type', string='03', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_04 = fields.Many2one('dl.salary.kpi.attendance.type', string='04', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_05 = fields.Many2one('dl.salary.kpi.attendance.type', string='05', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_06 = fields.Many2one('dl.salary.kpi.attendance.type', string='06', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_07 = fields.Many2one('dl.salary.kpi.attendance.type', string='07', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_08 = fields.Many2one('dl.salary.kpi.attendance.type', string='08', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_09 = fields.Many2one('dl.salary.kpi.attendance.type', string='09', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_10 = fields.Many2one('dl.salary.kpi.attendance.type', string='10', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_11 = fields.Many2one('dl.salary.kpi.attendance.type', string='11', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_12 = fields.Many2one('dl.salary.kpi.attendance.type', string='12', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_13 = fields.Many2one('dl.salary.kpi.attendance.type', string='13', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_14 = fields.Many2one('dl.salary.kpi.attendance.type', string='14', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_15 = fields.Many2one('dl.salary.kpi.attendance.type', string='15', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_16 = fields.Many2one('dl.salary.kpi.attendance.type', string='16', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_17 = fields.Many2one('dl.salary.kpi.attendance.type', string='17', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_18 = fields.Many2one('dl.salary.kpi.attendance.type', string='18', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_19 = fields.Many2one('dl.salary.kpi.attendance.type', string='19', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_20 = fields.Many2one('dl.salary.kpi.attendance.type', string='20', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_21 = fields.Many2one('dl.salary.kpi.attendance.type', string='21', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_22 = fields.Many2one('dl.salary.kpi.attendance.type', string='22', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_23 = fields.Many2one('dl.salary.kpi.attendance.type', string='23', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_24 = fields.Many2one('dl.salary.kpi.attendance.type', string='24', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_25 = fields.Many2one('dl.salary.kpi.attendance.type', string='25', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_26 = fields.Many2one('dl.salary.kpi.attendance.type', string='26', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_27 = fields.Many2one('dl.salary.kpi.attendance.type', string='27', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_28 = fields.Many2one('dl.salary.kpi.attendance.type', string='28', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_29 = fields.Many2one('dl.salary.kpi.attendance.type', string='29', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_30 = fields.Many2one('dl.salary.kpi.attendance.type', string='30', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_31 = fields.Many2one('dl.salary.kpi.attendance.type', string='31', domain="[('apply_to', 'in', ['normal', 'both'])]")

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

    # Các trường chấm công Làm thêm giờ (Overtime)
    ot_day_01 = fields.Many2one('dl.salary.kpi.attendance.type', string='01', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_02 = fields.Many2one('dl.salary.kpi.attendance.type', string='02', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_03 = fields.Many2one('dl.salary.kpi.attendance.type', string='03', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_04 = fields.Many2one('dl.salary.kpi.attendance.type', string='04', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_05 = fields.Many2one('dl.salary.kpi.attendance.type', string='05', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_06 = fields.Many2one('dl.salary.kpi.attendance.type', string='06', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_07 = fields.Many2one('dl.salary.kpi.attendance.type', string='07', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_08 = fields.Many2one('dl.salary.kpi.attendance.type', string='08', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_09 = fields.Many2one('dl.salary.kpi.attendance.type', string='09', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_10 = fields.Many2one('dl.salary.kpi.attendance.type', string='10', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_11 = fields.Many2one('dl.salary.kpi.attendance.type', string='11', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_12 = fields.Many2one('dl.salary.kpi.attendance.type', string='12', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_13 = fields.Many2one('dl.salary.kpi.attendance.type', string='13', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_14 = fields.Many2one('dl.salary.kpi.attendance.type', string='14', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_15 = fields.Many2one('dl.salary.kpi.attendance.type', string='15', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_16 = fields.Many2one('dl.salary.kpi.attendance.type', string='16', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_17 = fields.Many2one('dl.salary.kpi.attendance.type', string='17', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_18 = fields.Many2one('dl.salary.kpi.attendance.type', string='18', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_19 = fields.Many2one('dl.salary.kpi.attendance.type', string='19', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_20 = fields.Many2one('dl.salary.kpi.attendance.type', string='20', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_21 = fields.Many2one('dl.salary.kpi.attendance.type', string='21', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_22 = fields.Many2one('dl.salary.kpi.attendance.type', string='22', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_23 = fields.Many2one('dl.salary.kpi.attendance.type', string='23', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_24 = fields.Many2one('dl.salary.kpi.attendance.type', string='24', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_25 = fields.Many2one('dl.salary.kpi.attendance.type', string='25', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_26 = fields.Many2one('dl.salary.kpi.attendance.type', string='26', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_27 = fields.Many2one('dl.salary.kpi.attendance.type', string='27', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_28 = fields.Many2one('dl.salary.kpi.attendance.type', string='28', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_29 = fields.Many2one('dl.salary.kpi.attendance.type', string='29', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_30 = fields.Many2one('dl.salary.kpi.attendance.type', string='30', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_31 = fields.Many2one('dl.salary.kpi.attendance.type', string='31', domain="[('apply_to', 'in', ['overtime', 'both'])]")

    # Trường tổng hợp để phục vụ tìm kiếm/lọc
    attendance_type_ids = fields.Many2many(
        'dl.salary.kpi.attendance.type',
        compute='_compute_attendance_type_ids',
        store=True,
        string='Các loại công trong tháng'
    )

    # Các trường tổng hợp số lượng công
    total_n = fields.Float(string='Ngày', compute='_compute_totals', store=True)
    total_d = fields.Float(string='Đêm', compute='_compute_totals', store=True)
    total_p = fields.Float(string='Phép (P)', compute='_compute_totals', store=True)
    total_pl = fields.Float(string='Phép lễ (PL)', compute='_compute_totals', store=True)
    total_kp = fields.Float(string='Không phép (KP)', compute='_compute_totals', store=True)
    total_o = fields.Float(string='Nghỉ ốm (Ô)', compute='_compute_totals', store=True)
    total_dc = fields.Float(string='Đổi ca (ĐC)', compute='_compute_totals', store=True)
    total_co = fields.Float(string='Con ốm (CÔ)', compute='_compute_totals', store=True)

    # Các trường tổng hợp Làm thêm giờ
    total_ot_n = fields.Float(string='Giờ LT (Ngày)', compute='_compute_totals', store=True)
    total_ot_d = fields.Float(string='Giờ LT (Đêm)', compute='_compute_totals', store=True)
    total_ot_all = fields.Float(string='Tổng', compute='_compute_totals', store=True)

    # Các trường chi tiết Làm thêm giờ theo yêu cầu
    total_ot_n_normal = fields.Float(string='Giờ LT Ngày thường (N)', compute='_compute_totals', store=True)
    total_ot_d_normal = fields.Float(string='Giờ LT Ngày thường (Đ)', compute='_compute_totals', store=True)
    total_ot_n_sun = fields.Float(string='Giờ LT CN (Ngày)', compute='_compute_totals', store=True)
    total_ot_d_sun = fields.Float(string='Giờ LT CN (Đêm)', compute='_compute_totals', store=True)
    total_ot_n_holiday = fields.Float(string='Giờ LT Lễ (Ngày)', compute='_compute_totals', store=True)
    total_ot_d_holiday = fields.Float(string='Giờ LT Lễ (Đêm)', compute='_compute_totals', store=True)

    @api.depends('day_01', 'day_02', 'day_03', 'day_04', 'day_05', 'day_06', 'day_07', 'day_08', 'day_09', 'day_10',
                 'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20',
                 'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31',
                 'ot_day_01', 'ot_day_02', 'ot_day_03', 'ot_day_04', 'ot_day_05', 'ot_day_06', 'ot_day_07', 'ot_day_08', 'ot_day_09', 'ot_day_10',
                 'ot_day_11', 'ot_day_12', 'ot_day_13', 'ot_day_14', 'ot_day_15', 'ot_day_16', 'ot_day_17', 'ot_day_18', 'ot_day_19', 'ot_day_20',
                 'ot_day_21', 'ot_day_22', 'ot_day_23', 'ot_day_24', 'ot_day_25', 'ot_day_26', 'ot_day_27', 'ot_day_28', 'ot_day_29', 'ot_day_30', 'ot_day_31')
    def _compute_totals(self):
        for rec in self:
            n, d, p, pl, kp, o, dc, co = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            ot_n, ot_d = 0.0, 0.0
            ot_n_normal, ot_d_normal, ot_n_sun, ot_d_sun, ot_n_holiday, ot_d_holiday = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            for i in range(1, 32):
                # Công thường
                att = getattr(rec, f'day_{i:02d}')
                if att:
                    code = att.code
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
                
                # Làm thêm giờ
                ot_att = getattr(rec, f'ot_day_{i:02d}')
                if ot_att:
                    code = ot_att.code or ""
                    hours = ot_att.weight * 10
                    
                    if ot_att.ot_type == 'day':
                        ot_n += hours
                        if code == '0.5N': ot_n_normal += hours
                        elif code in ['CNN', 'CNN/2']: ot_n_sun += hours
                        elif code == 'LN': ot_n_holiday += hours
                    elif ot_att.ot_type == 'night':
                        ot_d += hours
                        if code == '0.5Đ': ot_d_normal += hours
                        elif code in ['CNĐ', 'CNĐ/2', 'CND/2']: ot_d_sun += hours
                        elif code == 'LĐ': ot_d_holiday += hours

            rec.total_n = n
            rec.total_d = d
            rec.total_p = p
            rec.total_pl = pl
            rec.total_kp = kp
            rec.total_o = o
            rec.total_dc = dc
            rec.total_co = co
            
            rec.total_ot_n = ot_n
            rec.total_ot_d = ot_d
            rec.total_ot_all = ot_n + ot_d
            
            rec.total_ot_n_normal = ot_n_normal
            rec.total_ot_d_normal = ot_d_normal
            rec.total_ot_n_sun = ot_n_sun
            rec.total_ot_d_sun = ot_d_sun
            rec.total_ot_n_holiday = ot_n_holiday
            rec.total_ot_d_holiday = ot_d_holiday

    @api.depends('day_01', 'day_02', 'day_03', 'day_04', 'day_05', 'day_06', 'day_07', 'day_08', 'day_09', 'day_10',
                 'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20',
                 'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31')
    def _compute_attendance_type_ids(self):
        for rec in self:
            types = []
            for i in range(1, 32):
                val = getattr(rec, f'day_{i:02d}')
                if val:
                    types.append(val.id)
            rec.attendance_type_ids = [(6, 0, list(set(types)))]

    @api.depends('month_id.date_month')
    def _compute_is_sunday(self):
        from calendar import monthrange
        from datetime import date
        for rec in self:
            if not rec.month_id.date_month:
                for i in range(1, 32):
                    rec[f'day_{i:02d}_is_sunday'] = False
                continue
                
            d_m = rec.month_id.date_month
            year, month = d_m.year, d_m.month
            last_day = monthrange(year, month)[1]
            
            for i in range(1, 32):
                field_name = f'day_{i:02d}_is_sunday'
                if i <= last_day:
                    d = date(year, month, i)
                    rec[field_name] = (d.weekday() == 6)
                else:
                    rec[field_name] = False

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
                    if current_day.code == 'Đ' and next_day.code == 'N':
                        raise ValidationError(_(
                            "Nhân viên %s: Lỗi quy tắc đổi ca tại ngày %02d-%02d. "
                            "Khi chuyển từ ca Ngày (Đ) sang ca Đêm (N), bắt buộc phải có ngày Đổi ca (ĐC) ở giữa."
                        ) % (rec.employee_name, i, i+1))

    @api.constrains('day_01', 'day_02', 'day_03', 'day_04', 'day_05', 'day_06', 'day_07', 'day_08', 'day_09', 'day_10',
                    'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20',
                    'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31')
    def _check_sunday_attendance(self):
        for rec in self:
            for i in range(1, 32):
                day_field = f'day_{i:02d}'
                is_sun_field = f'day_{i:02d}_is_sunday'
                if getattr(rec, day_field) and getattr(rec, is_sun_field):
                    raise ValidationError(_("Ngày %02d là Chủ Nhật. Không được phép chấm công thường vào ngày này. Vui lòng chấm vào phần Làm thêm giờ.") % i)

    @api.constrains('day_01', 'day_02', 'day_03', 'day_04', 'day_05', 'day_06', 'day_07', 'day_08', 'day_09', 'day_10',
                    'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20',
                    'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31',
                    'ot_day_01', 'ot_day_02', 'ot_day_03', 'ot_day_04', 'ot_day_05', 'ot_day_06', 'ot_day_07', 'ot_day_08', 'ot_day_09', 'ot_day_10',
                    'ot_day_11', 'ot_day_12', 'ot_day_13', 'ot_day_14', 'ot_day_15', 'ot_day_16', 'ot_day_17', 'ot_day_18', 'ot_day_19', 'ot_day_20',
                    'ot_day_21', 'ot_day_22', 'ot_day_23', 'ot_day_24', 'ot_day_25', 'ot_day_26', 'ot_day_27', 'ot_day_28', 'ot_day_29', 'ot_day_30', 'ot_day_31')
    def _check_departure_date_attendance(self):
        """
        Ràng buộc: Nếu nhân viên đã nghỉ việc (có dl_departure_date),
        thì không được phép có bất kỳ công nào sau ngày đó.
        """
        from datetime import date
        for rec in self:
            dep_date = rec.employee_id.dl_departure_date
            if not dep_date:
                continue
            
            month_date = rec.month_id.date_month
            if not month_date:
                continue
                
            year, month = month_date.year, month_date.month
            
            vals_to_clear = {}
            for i in range(1, 32):
                try:
                    d = date(year, month, i)
                except ValueError:
                    continue
                
                if d > dep_date:
                    if getattr(rec, f'day_{i:02d}'):
                        vals_to_clear[f'day_{i:02d}'] = False
                    if getattr(rec, f'ot_{i:02d}' if hasattr(rec, f'ot_{i:02d}') else f'ot_day_{i:02d}'):
                        vals_to_clear[f'ot_day_{i:02d}'] = False
            
            if vals_to_clear:
                # Dùng sudo().write để tránh lặp constraint vô tận nếu cần, 
                # nhưng ở đây ta chỉ cần xoá dữ liệu sai.
                # Lưu ý: rec.write sẽ kích hoạt lại constraint, nên ta kiểm tra vals_to_clear trước.
                rec.sudo().write(vals_to_clear)

