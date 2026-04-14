# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CombinedLog(models.Model):
    _name = 'dl.combined.log'
    _description = 'Cộng Công Lượng - Kết hợp Chấm công và Sản lượng'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Mã phiếu', required=True, copy=False, readonly=True, default=lambda self: _('Mới'))
    date = fields.Date(string='Ngày thực hiện', default=fields.Date.today(), required=True, tracking=True)
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
    
    batch_attendance_type_id = fields.Many2one(
        'dl.attendance.type', 
        string='Loại công mặc định',
        help="Chọn để áp dụng nhanh cho tất cả nhân viên."
    )

    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('confirmed', 'Đã xác nhận'),
    ], string='Trạng thái', default='draft', tracking=True)

    product_line_ids = fields.One2many(
        'dl.combined.product.line', 
        'combined_log_id', 
        string='Chi tiết sản phẩm'
    )
    
    worker_line_ids = fields.One2many(
        'dl.combined.worker.line', 
        'combined_log_id', 
        string='Chi tiết nhân sự'
    )

    # Links to standard models
    attendance_id = fields.Many2one('dl.daily.attendance', string='Phiếu chấm công gốc', readonly=True)
    production_log_id = fields.Many2one('dl.production.log', string='Bản ghi sản lượng gốc', readonly=True)

    _sql_constraints = [
        ('group_date_unique', 'unique(production_group_id, date)', 'Tổ này đã có phiếu Cộng Công Lượng cho ngày này!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Mới')) == _('Mới'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dl.combined.log') or '/'
        return super().create(vals_list)

    @api.onchange('production_group_id')
    def _onchange_production_group_id(self):
        if self.production_group_id:
            # 1. Prediction Logic for Shift (Type)
            last_log = self.env['dl.combined.log'].search([
                ('production_group_id', '=', self.production_group_id.id)
            ], order='date desc', limit=1)
            
            import datetime
            if last_log:
                self.date = last_log.date + datetime.timedelta(days=1)
                default_type = last_log.batch_attendance_type_id
            else:
                self.date = fields.Date.today()
                default_type = self.env['dl.attendance.type'].search([('code', '=', 'N')], limit=1)
            
            self.batch_attendance_type_id = default_type

            # 2. Load Workers
            lines = []
            for employee in self.production_group_id.member_ids:
                lines.append((0, 0, {
                    'employee_id': employee.id,
                    'attendance_type_id': default_type.id if default_type else False,
                    'worked_hours': 1.0,
                    'is_borrowed': False
                }))
            self.worker_line_ids = [(5, 0, 0)] + lines

    @api.onchange('batch_attendance_type_id')
    def _onchange_batch_attendance_type_id(self):
        if self.batch_attendance_type_id and self.worker_line_ids:
            for line in self.worker_line_ids:
                line.attendance_type_id = self.batch_attendance_type_id

    def action_confirm(self):
        self.ensure_one()
        if not self.worker_line_ids:
            raise ValidationError(_("Vui lòng nhập danh sách nhân sự."))

        # 1. Sync to dl.daily.attendance
        attendance_vals = {
            'date': self.date,
            'production_group_id': self.production_group_id.id,
            'batch_attendance_type_id': self.batch_attendance_type_id.id,
            'state': 'confirmed',
            'attendance_line_ids': [(0, 0, {
                'employee_id': w.employee_id.id,
                'attendance_type_id': w.attendance_type_id.id,
            }) for w in self.worker_line_ids]
        }
        
        # Check for existing records to update or create
        existing_att = self.env['dl.daily.attendance'].search([
            ('production_group_id', '=', self.production_group_id.id),
            ('date', '=', self.date)
        ], limit=1)
        
        if existing_att:
            existing_att.attendance_line_ids.unlink()
            existing_att.write(attendance_vals)
            self.attendance_id = existing_att
        else:
            self.attendance_id = self.env['dl.daily.attendance'].create(attendance_vals)

        # 2. Sync to dl.production.log
        production_vals = {
            'date': self.date,
            'production_group_id': self.production_group_id.id,
            'state': 'confirmed',
            'product_line_ids': [(0, 0, {
                'product_id': p.product_id.id,
                'quantity': p.quantity,
                'is_re_ep_film': p.is_re_ep_film,
            }) for p in self.product_line_ids],
            'worker_line_ids': [(0, 0, {
                'employee_id': w.employee_id.id,
                'worked_hours': w.worked_hours,
            }) for w in self.worker_line_ids]
        }
        
        existing_prod = self.env['dl.production.log'].search([
            ('production_group_id', '=', self.production_group_id.id),
            ('date', '=', self.date)
        ], limit=1)
        
        if existing_prod:
            existing_prod.product_line_ids.unlink()
            existing_prod.worker_line_ids.unlink()
            existing_prod.write(production_vals)
            self.production_log_id = existing_prod
        else:
            self.production_log_id = self.env['dl.production.log'].create(production_vals)

        self.state = 'confirmed'

    def action_draft(self):
        self.state = 'draft'
        if self.attendance_id:
            self.attendance_id.state = 'draft'
        if self.production_log_id:
            self.production_log_id.state = 'draft'

class CombinedProductLine(models.Model):
    _name = 'dl.combined.product.line'
    _description = 'Chi tiết sản phẩm cộng dồn'
    _order = 'id'

    combined_log_id = fields.Many2one('dl.combined.log', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Sản phẩm', required=True)
    quantity = fields.Float(string='Số lượng', default=1.0)
    is_re_ep_film = fields.Boolean(string='Ép lại 1 mặt')

class CombinedWorkerLine(models.Model):
    _name = 'dl.combined.worker.line'
    _description = 'Chi tiết nhân sự cộng dồn'
    _order = 'is_borrowed, id'

    combined_log_id = fields.Many2one('dl.combined.log', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True)
    attendance_type_id = fields.Many2one('dl.attendance.type', string='Loại công', required=True)
    worked_hours = fields.Float(string='Số công h/tế', default=1.0)
    is_borrowed = fields.Boolean(string='Mượn người', default=False)
    
    borrowed_badge = fields.Char(string='Trạng thái', compute='_compute_borrowed_badge')

    def _compute_borrowed_badge(self):
        for rec in self:
            rec.borrowed_badge = _('Mượn người') if rec.is_borrowed else _('Biên chế')

    @api.onchange('attendance_type_id')
    def _onchange_attendance_type_id(self):
        if self.attendance_type_id:
            self.worked_hours = self.attendance_type_id.work_value

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id and self.combined_log_id.production_group_id:
            # Tự động xác định mượn người (An toàn)
            source_id = self.employee_id.x_source_group_id.id or 0
            group_id = self.combined_log_id.production_group_id.id or 0
            self.is_borrowed = source_id != group_id
