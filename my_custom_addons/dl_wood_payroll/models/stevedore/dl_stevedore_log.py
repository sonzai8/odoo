# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StevedoreLog(models.Model):
    _name = 'dl.stevedore.log'
    _description = 'Phiếu Bốc Vác / Tài xế'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Mã phiếu', required=True, copy=False, readonly=True, default=lambda self: _('Mới'))
    date = fields.Date(string='Ngày thực hiện', default=fields.Date.today(), required=True, tracking=True)
    task_id = fields.Many2one('dl.stevedore.task', string='Loại công việc', required=True, tracking=True)
    production_group_id = fields.Many2one('dl.production.group', string='Tổ sản xuất', tracking=True)
    quantity = fields.Float(string='Số lượng', default=1.0, tracking=True)
    unit_price = fields.Float(related='task_id.unit_price', readonly=True, store=True)
    total_amount = fields.Float(string='Tổng tiền', compute='_compute_total_amount', store=True, tracking=True)
    
    line_ids = fields.One2many('dl.stevedore.log.line', 'log_id', string='Chi tiết', copy=True)
    worker_ids = fields.Many2many('hr.employee', string='Nhân viên tham gia', 
                                  compute='_compute_worker_ids', inverse='_inverse_worker_ids', 
                                  help='Chọn nhanh nhân viên', required=True, store=True)
    
    amount_per_worker = fields.Float(string='Tiền mỗi người', compute='_compute_amount_per_worker', store=True)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)
    
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
    ], string='Trạng thái', default='draft', tracking=True)

    @api.depends('quantity', 'unit_price')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.quantity * (rec.unit_price or 0.0)

    @api.depends('total_amount', 'line_ids.quantity')
    def _compute_amount_per_worker(self):
        for rec in self:
            total_qty = sum(rec.line_ids.mapped('quantity'))
            if total_qty > 0:
                amount_per_unit = rec.total_amount / total_qty
                for line in rec.line_ids:
                    line.amount = line.quantity * amount_per_unit
                # Hiển thị số tiền trung bình cho 1 công (để tham khảo)
                rec.amount_per_worker = amount_per_unit
            else:
                for line in rec.line_ids:
                    line.amount = 0.0
                rec.amount_per_worker = 0.0

    @api.depends('line_ids.employee_id')
    def _compute_worker_ids(self):
        for rec in self:
            rec.worker_ids = rec.line_ids.mapped('employee_id')

    def _inverse_worker_ids(self):
        for rec in self:
            current_employees = rec.line_ids.mapped('employee_id')
            new_employees = rec.worker_ids
            
            # Remove
            to_remove = rec.line_ids.filtered(lambda l: l.employee_id not in new_employees)
            if to_remove:
                rec.line_ids -= to_remove
            
            # Add
            to_add = new_employees - current_employees
            for emp in to_add:
                rec.line_ids = [(0, 0, {'employee_id': emp.id})]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Mới')) == _('Mới'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dl.stevedore.log') or '/'
        return super().create(vals_list)

    def action_confirm(self):
        self.ensure_one()
        if not self.line_ids:
            raise ValidationError(_("Vui lòng chọn nhân viên tham gia."))
        self.write({'state': 'confirmed'})
        self._auto_create_attendance()

    def action_draft(self):
        self.write({'state': 'draft'})

    def _auto_create_attendance(self):
        """Tự động sinh chấm công nếu nhân viên chưa có công trong ngày"""
        AttendanceLine = self.env['dl.daily.attendance.line']
        Attendance = self.env['dl.daily.attendance']
        
        default_type = self.env.ref('dl_wood_payroll.attendance_type_n', False)
        if not default_type:
            default_type = self.env['dl.attendance.type'].search([('code', '=', 'N')], limit=1)

        for line in self.line_ids:
            employee = line.employee_id
            exists = AttendanceLine.search_count([
                ('employee_id', '=', employee.id),
                ('date', '=', self.date),
                ('actual_work', '>=', 0.1)
            ])
            if not exists:
                group = employee.x_source_group_id
                if not group:
                    continue
                
                att = Attendance.search([
                    ('production_group_id', '=', group.id),
                    ('date', '=', self.date)
                ], limit=1)
                
                if not att:
                    att = Attendance.create({
                        'production_group_id': group.id,
                        'date': self.date,
                        'state': 'confirmed'
                    })
                
                AttendanceLine.create({
                    'attendance_id': att.id,
                    'employee_id': employee.id,
                    'attendance_type_id': default_type.id if default_type else False,
                })

class StevedoreLogLine(models.Model):
    _name = 'dl.stevedore.log.line'
    _description = 'Chi tiết nhân viên bốc vác'

    log_id = fields.Many2one('dl.stevedore.log', string='Phiếu bốc vác', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True)
    x_source_group_id = fields.Many2one(related='employee_id.x_source_group_id', string='Tổ biên chế', store=True)
    quantity = fields.Float(string='Số công', default=1.0, digits=(12, 1))
    amount = fields.Float(string='Số tiền nhận', compute='_compute_amount_line', store=True)
    date = fields.Date(related='log_id.date', store=True, index=True)
    currency_id = fields.Many2one(related='log_id.currency_id', store=True)

    @api.depends('quantity', 'log_id.total_amount', 'log_id.line_ids.quantity')
    def _compute_amount_line(self):
        for line in self:
            if not line.log_id:
                line.amount = 0.0
                continue
            total_qty = sum(line.log_id.line_ids.mapped('quantity'))
            if total_qty > 0:
                line.amount = (line.quantity * line.log_id.total_amount) / total_qty
            else:
                line.amount = 0.0

    @api.constrains('quantity')
    def _check_quantity(self):
        for line in self:
            if line.quantity < 0.1 or line.quantity > 1.0:
                raise ValidationError(_("Số công của mỗi nhân viên phải nằm trong khoảng từ 0.1 đến 1.0."))
