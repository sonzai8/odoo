# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StevedoreService(models.Model):
    _name = 'dl.stevedore.service'
    _description = 'Danh mục công việc bốc vác'
    _order = 'name'

    name = fields.Char(string='Tên công việc', required=True)
    default_unit_price = fields.Float(string='Đơn giá mặc định')
    uom_id = fields.Char(string='Đơn vị tính', help="VD: Chuyến, m3, Tấn...")
    active = fields.Boolean(default=True)

class StevedoreLog(models.Model):
    _name = 'dl.stevedore.log'
    _description = 'Phiếu khoán việc - Bốc vác/Tài xế'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Mã phiếu', required=True, copy=False, readonly=True, default=lambda self: _('Mới'))
    date = fields.Date(string='Ngày thực hiện', default=fields.Date.today(), required=True, tracking=True)
    
    service_id = fields.Many2one('dl.stevedore.service', string='Loại công việc', tracking=True)
    manual_service_name = fields.Char(string='Tên việc (Nhập tay)', tracking=True)
    service_name = fields.Char(string='Tên hiển thị', compute='_compute_service_name', store=True)

    unit_price = fields.Float(string='Đơn giá', tracking=True)
    quantity = fields.Float(string='Số lượng', default=1.0, tracking=True)
    total_amount = fields.Float(string='Tổng tiền khoán', compute='_compute_total_amount', store=True, readonly=False, tracking=True)
    
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('confirmed', 'Đã xác nhận'),
    ], string='Trạng thái', default='draft', tracking=True)

    worker_line_ids = fields.One2many(
        'dl.stevedore.log.line', 
        'stevedore_log_id', 
        string='Chi tiết chia tiền'
    )

    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)

    @api.depends('service_id', 'manual_service_name')
    def _compute_service_name(self):
        for rec in self:
            rec.service_name = rec.service_id.name or rec.manual_service_name or _('Cần nhập tên việc')

    @api.depends('unit_price', 'quantity')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.unit_price * rec.quantity

    @api.onchange('service_id')
    def _onchange_service_id(self):
        if self.service_id:
            self.unit_price = self.service_id.default_unit_price
            if not self.manual_service_name:
                self.manual_service_name = self.service_id.name

    @api.onchange('total_amount', 'worker_line_ids')
    def _onchange_distribute_amount(self):
        """Tự động chia tiền khi tổng tiền hoặc danh sách nhân viên thay đổi"""
        if self.state != 'draft':
            return
            
        auto_lines = self.worker_line_ids.filtered(lambda l: not l.is_manual_amount)
        if not auto_lines:
            return

        manual_sum = sum(self.worker_line_ids.filtered(lambda l: l.is_manual_amount).mapped('amount'))
        remaining_amount = self.total_amount - manual_sum
        
        total_attendance = sum(auto_lines.mapped('attendance_value'))
        
        if total_attendance > 0:
            for line in auto_lines:
                line.amount = round((line.attendance_value / total_attendance) * remaining_amount)
        else:
            # Chia đều nếu không có hệ số công
            amount_per = round(remaining_amount / len(auto_lines))
            for line in auto_lines:
                line.amount = amount_per

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Mới')) == _('Mới'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dl.stevedore.log') or '/'
        return super().create(vals_list)

    def action_divide_equally(self):
        """Giữ lại để tương thích hoặc dùng khi muốn reset toàn bộ về chia đều"""
        self.ensure_one()
        for line in self.worker_line_ids:
            line.is_manual_amount = False
            line.attendance_value = 1.0
        self._onchange_distribute_amount()

    def action_confirm(self):
        self.ensure_one()
        if not self.worker_line_ids:
            raise ValidationError(_("Vui lòng thêm nhân viên tham gia."))
        
        total_lines = sum(self.worker_line_ids.mapped('amount'))
        if abs(self.total_amount - total_lines) > 10:
            raise ValidationError(_("Tổng tiền chia cho nhân viên (%(total_lines)s) không khớp với Tổng tiền khoán (%(total_amount)s). Sai lệch cho phép tối đa 10đ.") % {
                'total_lines': "{:,.0f}".format(total_lines),
                'total_amount': "{:,.0f}".format(self.total_amount)
            })
        
        self.write({'state': 'confirmed'})
        self._auto_create_attendance()

    def _auto_create_attendance(self):
        """Tự động sinh công nếu nhân viên chưa có chấm công trong ngày"""
        AttendanceLine = self.env['dl.daily.attendance.line']
        Attendance = self.env['dl.daily.attendance']
        
        # Lấy loại công mặc định (N)
        default_type = self.env.ref('dl_wood_payroll.attendance_type_n', False)
        if not default_type:
            default_type = self.env['dl.attendance.type'].search([('code', '=', 'N')], limit=1)

        for line in self.worker_line_ids:
            # Kiểm tra xem nhân viên đã có công trong ngày chưa
            exists = AttendanceLine.search_count([
                ('employee_id', '=', line.employee_id.id),
                ('date', '=', self.date),
                ('actual_work', '>=', 0.1)
            ])
            if not exists:
                # Tìm hoặc tạo phiếu chấm công cho tổ gốc của nhân viên
                group = line.employee_id.x_source_group_id
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
                    'employee_id': line.employee_id.id,
                    'attendance_type_id': default_type.id if default_type else False,
                })

    def action_draft(self):
        self.write({'state': 'draft'})

class StevedoreLogLine(models.Model):
    _name = 'dl.stevedore.log.line'
    _description = 'Chi tiết chia tiền bốc vác'

    stevedore_log_id = fields.Many2one('dl.stevedore.log', string='Phiếu khoán', ondelete='cascade')
    date = fields.Date(related='stevedore_log_id.date', store=True, index=True)
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True)
    
    attendance_value = fields.Float(string='Hệ số công', default=1.0)
    amount = fields.Float(string='Số tiền nhận', required=True)
    is_manual_amount = fields.Boolean(string='Nhập tay', default=False)
    
    note = fields.Char(string='Ghi chú')
    currency_id = fields.Many2one(related='stevedore_log_id.currency_id', store=True)

    @api.onchange('amount')
    def _onchange_manual_amount(self):
        if self.amount:
            self.is_manual_amount = True

    @api.onchange('attendance_value')
    def _onchange_attendance_value(self):
        # Nếu thay đổi hệ số công thì gỡ bỏ đánh dấu nhập tay để hệ thống tính lại
        self.is_manual_amount = False

