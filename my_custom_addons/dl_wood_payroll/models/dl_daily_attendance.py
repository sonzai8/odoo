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
    ], string='Trạng thái', default='draft', tracking=True)

    attendance_line_ids = fields.One2many(
        'dl.daily.attendance.line', 
        'attendance_id', 
        string='Chi tiết chấm công'
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
            # Smart Load Logic: Get members from group
            # Use safety search if XML ref is not found
            default_type = self.env.ref('dl_wood_payroll.attendance_type_n', False)
            if not default_type:
                default_type = self.env['dl.attendance.type'].search([('code', '=', 'N')], limit=1)
            
            lines = []
            for employee in self.production_group_id.member_ids:
                lines.append((0, 0, {
                    'employee_id': employee.id,
                    'attendance_type_id': default_type.id if default_type else False,
                    'actual_work': default_type.work_value if default_type else 1.0,
                }))
            # Reset lines and apply new ones
            self.attendance_line_ids = [(5, 0, 0)] + lines

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

    @api.depends('attendance_type_id')
    def _compute_actual_work(self):
        for line in self:
            if line.attendance_type_id:
                line.actual_work = line.attendance_type_id.work_value
            else:
                line.actual_work = 0.0

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
