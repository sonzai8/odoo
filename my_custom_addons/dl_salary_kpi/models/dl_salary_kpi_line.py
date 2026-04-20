# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SalaryKpiLine(models.Model):
    _name = 'dl.salary.kpi.line'
    _description = 'Chi tiết lương & KPI nhân viên'
    _order = 'is_disabled, department_id, work_group_id, employee_name'

    month_id = fields.Many2one('dl.salary.kpi.month', string='Tháng lương', ondelete='cascade', required=True)
    kpi_employee_id = fields.Many2one('dl.salary.kpi.employee', string='Nhân viên KPI')
    is_disabled = fields.Boolean(string='Không cân đối', default=False)
    employee_id = fields.Many2one('hr.employee', related='kpi_employee_id.employee_id', string='Nhân viên hệ thống', store=True)
    employee_name = fields.Char(string='Họ và tên', store=True, readonly=False, compute='_compute_employee_details')
    identification_id = fields.Char(string='Số CCCD', store=True, readonly=False, compute='_compute_employee_details')
    department_id = fields.Many2one('hr.department', string='Xưởng/Phòng ban', store=True, readonly=False, compute='_compute_employee_details')
    work_group_id = fields.Many2one('dl.production.group', string='Tổ biên chế', store=True, readonly=False, compute='_compute_employee_details')
    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác')
    ], related='kpi_employee_id.gender', string='Giới tính', store=True)
    
    meal_allowance = fields.Monetary(string='Hỗ trợ ăn ca', currency_field='currency_id')
    women_allowance = fields.Monetary(string='Trợ cấp phụ nữ', currency_field='currency_id')
    allowance_amount = fields.Monetary(string='Các khoản hỗ trợ khác', currency_field='currency_id')
    bonus_amount = fields.Monetary(string='Thưởng tháng', currency_field='currency_id')
    kpi_score = fields.Float(string='Điểm KPI', default=100.0)
    
    notes = fields.Text(string='Ghi chú')
    currency_id = fields.Many2one(related='month_id.currency_id', readonly=True)
    
    attendance_ids = fields.One2many('dl.salary.kpi.attendance.line', 'month_line_id', string='Chi tiết chấm công')

    # Matrix View Fields (1-31)
    day_01 = fields.Many2one('dl.salary.kpi.attendance.type', string='01', compute='_compute_days', inverse='_inverse_day_01')
    day_02 = fields.Many2one('dl.salary.kpi.attendance.type', string='02', compute='_compute_days', inverse='_inverse_day_02')
    day_03 = fields.Many2one('dl.salary.kpi.attendance.type', string='03', compute='_compute_days', inverse='_inverse_day_03')
    day_04 = fields.Many2one('dl.salary.kpi.attendance.type', string='04', compute='_compute_days', inverse='_inverse_day_04')
    day_05 = fields.Many2one('dl.salary.kpi.attendance.type', string='05', compute='_compute_days', inverse='_inverse_day_05')
    day_06 = fields.Many2one('dl.salary.kpi.attendance.type', string='06', compute='_compute_days', inverse='_inverse_day_06')
    day_07 = fields.Many2one('dl.salary.kpi.attendance.type', string='07', compute='_compute_days', inverse='_inverse_day_07')
    day_08 = fields.Many2one('dl.salary.kpi.attendance.type', string='08', compute='_compute_days', inverse='_inverse_day_08')
    day_09 = fields.Many2one('dl.salary.kpi.attendance.type', string='09', compute='_compute_days', inverse='_inverse_day_09')
    day_10 = fields.Many2one('dl.salary.kpi.attendance.type', string='10', compute='_compute_days', inverse='_inverse_day_10')
    day_11 = fields.Many2one('dl.salary.kpi.attendance.type', string='11', compute='_compute_days', inverse='_inverse_day_11')
    day_12 = fields.Many2one('dl.salary.kpi.attendance.type', string='12', compute='_compute_days', inverse='_inverse_day_12')
    day_13 = fields.Many2one('dl.salary.kpi.attendance.type', string='13', compute='_compute_days', inverse='_inverse_day_13')
    day_14 = fields.Many2one('dl.salary.kpi.attendance.type', string='14', compute='_compute_days', inverse='_inverse_day_14')
    day_15 = fields.Many2one('dl.salary.kpi.attendance.type', string='15', compute='_compute_days', inverse='_inverse_day_15')
    day_16 = fields.Many2one('dl.salary.kpi.attendance.type', string='16', compute='_compute_days', inverse='_inverse_day_16')
    day_17 = fields.Many2one('dl.salary.kpi.attendance.type', string='17', compute='_compute_days', inverse='_inverse_day_17')
    day_18 = fields.Many2one('dl.salary.kpi.attendance.type', string='18', compute='_compute_days', inverse='_inverse_day_18')
    day_19 = fields.Many2one('dl.salary.kpi.attendance.type', string='19', compute='_compute_days', inverse='_inverse_day_19')
    day_20 = fields.Many2one('dl.salary.kpi.attendance.type', string='20', compute='_compute_days', inverse='_inverse_day_20')
    day_21 = fields.Many2one('dl.salary.kpi.attendance.type', string='21', compute='_compute_days', inverse='_inverse_day_21')
    day_22 = fields.Many2one('dl.salary.kpi.attendance.type', string='22', compute='_compute_days', inverse='_inverse_day_22')
    day_23 = fields.Many2one('dl.salary.kpi.attendance.type', string='23', compute='_compute_days', inverse='_inverse_day_23')
    day_24 = fields.Many2one('dl.salary.kpi.attendance.type', string='24', compute='_compute_days', inverse='_inverse_day_24')
    day_25 = fields.Many2one('dl.salary.kpi.attendance.type', string='25', compute='_compute_days', inverse='_inverse_day_25')
    day_26 = fields.Many2one('dl.salary.kpi.attendance.type', string='26', compute='_compute_days', inverse='_inverse_day_26')
    day_27 = fields.Many2one('dl.salary.kpi.attendance.type', string='27', compute='_compute_days', inverse='_inverse_day_27')
    day_28 = fields.Many2one('dl.salary.kpi.attendance.type', string='28', compute='_compute_days', inverse='_inverse_day_28')
    day_29 = fields.Many2one('dl.salary.kpi.attendance.type', string='29', compute='_compute_days', inverse='_inverse_day_29')
    day_30 = fields.Many2one('dl.salary.kpi.attendance.type', string='30', compute='_compute_days', inverse='_inverse_day_30')
    day_31 = fields.Many2one('dl.salary.kpi.attendance.type', string='31', compute='_compute_days', inverse='_inverse_day_31')

    total_work_days = fields.Float(string='Tổng công', compute='_compute_total_stats', store=True)
    total_day_hours = fields.Float(string='Giờ ngày', compute='_compute_total_stats', store=True)
    total_night_hours = fields.Float(string='Giờ đêm', compute='_compute_total_stats', store=True)
    total_overtime_hours = fields.Float(string='Tổng OT', compute='_compute_total_stats', store=True)

    total_salary_balance = fields.Monetary(
        string='Tổng lương cân đối', 
        compute='_compute_total_balance', 
        store=True, 
        currency_field='currency_id'
    )

    @api.depends('attendance_ids', 'attendance_ids.attendance_type_id')
    def _compute_days(self):
        for rec in self:
            att_map = {att.day: att.attendance_type_id.id for att in rec.attendance_ids}
            for i in range(1, 32):
                setattr(rec, f'day_{i:02d}', att_map.get(i, False))

    def _update_day(self, day, att_type):
        self.ensure_one()
        existing = self.attendance_ids.filtered(lambda l: l.day == day)
        if existing:
            if att_type:
                existing.attendance_type_id = att_type.id
            else:
                existing.unlink()
        elif att_type:
            self.env['dl.salary.kpi.attendance.line'].create({
                'month_line_id': self.id,
                'day': day,
                'attendance_type_id': att_type.id,
            })

    def _inverse_day_01(self): self._update_day(1, self.day_01)
    def _inverse_day_02(self): self._update_day(2, self.day_02)
    def _inverse_day_03(self): self._update_day(3, self.day_03)
    def _inverse_day_04(self): self._update_day(4, self.day_04)
    def _inverse_day_05(self): self._update_day(5, self.day_05)
    def _inverse_day_06(self): self._update_day(6, self.day_06)
    def _inverse_day_07(self): self._update_day(7, self.day_07)
    def _inverse_day_08(self): self._update_day(8, self.day_08)
    def _inverse_day_09(self): self._update_day(9, self.day_09)
    def _inverse_day_10(self): self._update_day(10, self.day_10)
    def _inverse_day_11(self): self._update_day(11, self.day_11)
    def _inverse_day_12(self): self._update_day(12, self.day_12)
    def _inverse_day_13(self): self._update_day(13, self.day_13)
    def _inverse_day_14(self): self._update_day(14, self.day_14)
    def _inverse_day_15(self): self._update_day(15, self.day_15)
    def _inverse_day_16(self): self._update_day(16, self.day_16)
    def _inverse_day_17(self): self._update_day(17, self.day_17)
    def _inverse_day_18(self): self._update_day(18, self.day_18)
    def _inverse_day_19(self): self._update_day(19, self.day_19)
    def _inverse_day_20(self): self._update_day(20, self.day_20)
    def _inverse_day_21(self): self._update_day(21, self.day_21)
    def _inverse_day_22(self): self._update_day(22, self.day_22)
    def _inverse_day_23(self): self._update_day(23, self.day_23)
    def _inverse_day_24(self): self._update_day(24, self.day_24)
    def _inverse_day_25(self): self._update_day(25, self.day_25)
    def _inverse_day_26(self): self._update_day(26, self.day_26)
    def _inverse_day_27(self): self._update_day(27, self.day_27)
    def _inverse_day_28(self): self._update_day(28, self.day_28)
    def _inverse_day_29(self): self._update_day(29, self.day_29)
    def _inverse_day_30(self): self._update_day(30, self.day_30)
    def _inverse_day_31(self): self._update_day(31, self.day_31)

    @api.depends('kpi_employee_id')
    def _compute_employee_details(self):
        for rec in self:
            if rec.kpi_employee_id:
                rec.employee_name = rec.kpi_employee_id.name
                rec.identification_id = rec.kpi_employee_id.identification_id
                rec.department_id = rec.kpi_employee_id.department_id
                rec.work_group_id = rec.kpi_employee_id.work_group_id
            else:
                rec.employee_name = rec.employee_name or ''
                rec.identification_id = rec.identification_id or ''

    @api.onchange('kpi_employee_id')
    def _onchange_kpi_employee_id(self):
        if self.kpi_employee_id:
            self.employee_name = self.kpi_employee_id.name
            self.identification_id = self.kpi_employee_id.identification_id
            self.department_id = self.kpi_employee_id.department_id
            self.work_group_id = self.kpi_employee_id.work_group_id
            # Note: Attendance pre-filling will be handled in the month action

    @api.depends('allowance_amount', 'bonus_amount', 'meal_allowance', 'women_allowance')
    def _compute_total_balance(self):
        for rec in self:
            rec.total_salary_balance = rec.allowance_amount + rec.bonus_amount + rec.meal_allowance + rec.women_allowance

    @api.depends('attendance_ids', 'attendance_ids.attendance_type_id')
    def _compute_total_stats(self):
        for rec in self:
            total_work = 0.0
            total_day = 0.0
            total_night = 0.0
            total_ot = 0.0
            for att in rec.attendance_ids:
                if att.attendance_type_id:
                    total_work += att.attendance_type_id.num_work
                    total_day += att.attendance_type_id.day_hour
                    total_night += att.attendance_type_id.night_hour
                    total_ot += att.attendance_type_id.default_overtime
            rec.total_work_days = total_work
            rec.total_day_hours = total_day
            rec.total_night_hours = total_night
            rec.total_overtime_hours = total_ot
