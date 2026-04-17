# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class DailyAttendance(models.Model):
    _name = 'dl.daily.attendance'
    _description = 'Phiếu chấm công theo tổ'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Mã phiếu', required=True, copy=False, readonly=True, default=lambda self: _('Mới'))
    date = fields.Date(string='Ngày chấm công', default=fields.Date.today(), required=True, tracking=True)
    production_group_id = fields.Many2one(
        'dl.production.group', 
        string='Tổ sản xuất', 
        required=True, 
        tracking=True
    )
    department_id = fields.Many2one(
        related='production_group_id.department_id', 
        string='Công đoạn', 
        store=True, 
        readonly=True
    )
    
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('confirmed', 'Đã xác nhận'),
    ], string='Trạng thái', default='confirmed', tracking=True)

    attendance_line_ids = fields.One2many(
        'dl.daily.attendance.line', 
        'attendance_id', 
        string='Chi tiết chấm công'
    )

    batch_attendance_type_id = fields.Many2one(
        'dl.attendance.type', 
        string='Loại công mặc định',
        help="Chọn để áp dụng nhanh loại công này cho tất cả nhân viên trong danh sách bên dưới."
    )

    _sql_constraints = [
        ('group_date_unique', 'unique(production_group_id, date)', 'Tổ này đã được chấm công cho ngày này!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Mới')) == _('Mới'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dl.daily.attendance') or '/'
        return super().create(vals_list)

    @api.onchange('production_group_id')
    def _onchange_production_group_id(self):
        if self.production_group_id:
            # 1. Prediction Logic: Look for the last record of this group
            last_attendance = self.env['dl.daily.attendance'].search([
                ('production_group_id', '=', self.production_group_id.id)
            ], order='date desc', limit=1)

            # 2. Smart Date: If found, next date = last + 1. Else, today.
            import datetime
            if last_attendance:
                self.date = last_attendance.date + datetime.timedelta(days=1)
                # 3. Smart Type: Get type from the first line of last attendance
                default_type = last_attendance.attendance_line_ids[0].attendance_type_id if last_attendance.attendance_line_ids else False
                if not default_type:
                    # Fallback to local default if last attendance was empty
                    default_type = self.env.ref('dl_wood_payroll.attendance_type_n', False)
                    if not default_type:
                        default_type = self.env['dl.attendance.type'].search([('code', '=', 'N')], limit=1)
            else:
                self.date = fields.Date.today()
                default_type = self.env.ref('dl_wood_payroll.attendance_type_n', False)
                if not default_type:
                    default_type = self.env['dl.attendance.type'].search([('code', '=', 'N')], limit=1)

            # 4. Set Batch Type
            self.batch_attendance_type_id = default_type

            # 5. Smart Load Logic: Populate lines
            lines = []
            for employee in self.production_group_id.member_ids:
                lines.append((0, 0, {
                    'employee_id': employee.id,
                    'attendance_type_id': default_type.id if default_type else False,
                    'actual_work': default_type.work_value if default_type else 1.0,
                }))
            # Reset lines and apply new ones
            self.attendance_line_ids = [(5, 0, 0)] + lines

    @api.onchange('batch_attendance_type_id')
    def _onchange_batch_attendance_type_id(self):
        if self.batch_attendance_type_id and self.attendance_line_ids:
            for line in self.attendance_line_ids:
                line.attendance_type_id = self.batch_attendance_type_id

    def action_confirm(self):
        for rec in self:
            if not rec.attendance_line_ids:
                raise ValidationError(_("Vui lòng nhập chi tiết chấm công trước khi xác nhận."))
        self.write({'state': 'confirmed'})

    def action_draft(self):
        self.write({'state': 'draft'})


class DailyAttendanceLine(models.Model):
    _name = 'dl.daily.attendance.line'
    _description = 'Chi tiết chấm công nhân viên'
    _order = 'date desc, employee_id'

    attendance_id = fields.Many2one('dl.daily.attendance', string='Phiếu chấm công', ondelete='cascade')
    date = fields.Date(related='attendance_id.date', store=True, index=True)
    production_group_id = fields.Many2one(related='attendance_id.production_group_id', store=True, index=True)
    
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True)
    attendance_type_id = fields.Many2one('dl.attendance.type', string='Loại công', required=True)
    actual_work = fields.Float(string='Công thực tế', digits=(16, 1), store=True, compute='_compute_actual_work')
    
    audit_state = fields.Selection([
        ('normal', 'Bình thường'),
        ('missing_output', 'Thiếu sản lượng'),
        ('over_worked', 'Vượt định mức')
    ], string='Kiểm tra dữ liệu', compute='_compute_audit_state', store=False)

    def _compute_audit_state(self):
        for line in self:
            state = 'normal'
            if line.date and line.employee_id:
                # 1. Kiểm tra thiếu sản lượng: Có tham gia sản xuất không?
                log_count = self.env['dl.worker.log.line'].search_count([
                    ('employee_id', '=', line.employee_id.id),
                    ('production_log_id.date', '=', line.date)
                ])
                if line.actual_work > 0 and log_count == 0:
                    state = 'missing_output'
                
                # 2. Kiểm tra vượt định mức: Tổng công trong ngày có > 1.0 không?
                total_work = sum(self.env['dl.daily.attendance.line'].search([
                    ('employee_id', '=', line.employee_id.id),
                    ('date', '=', line.date)
                ]).mapped('actual_work'))
                if total_work > 1.0:
                    state = 'over_worked'
                    
            line.audit_state = state

    @api.depends('attendance_type_id')
    def _compute_actual_work(self):
        for line in self:
            if line.attendance_type_id:
                line.actual_work = line.attendance_type_id.work_value
            else:
                line.actual_work = 0.0

    @api.onchange('attendance_type_id')
    def _onchange_attendance_type_id(self):
        if self.attendance_type_id:
            self.actual_work = self.attendance_type_id.work_value
        else:
            self.actual_work = 0.0

    @api.constrains('employee_id', 'actual_work', 'date')
    def _check_duplicate_attendance(self):
        for line in self:
            if line.actual_work >= 1.0:
                # Tìm xem có bản ghi 1.0 nào khác cho nhân viên này cùng ngày không
                other_lines = self.search([
                    ('employee_id', '=', line.employee_id.id),
                    ('date', '=', line.date),
                    ('actual_work', '>=', 1.0),
                    ('id', '!=', line.id)
                ])
                if other_lines:
                    raise ValidationError(_("Nhân viên %s đã được chấm công Full công (>= 1.0) ở một tổ khác trong ngày %s!") % 
                                          (line.employee_id.name, line.date))
