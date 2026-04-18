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
    
    is_kcs_stage = fields.Boolean(string='Là KCS', compute='_compute_stage_flags')
    is_film_stage = fields.Boolean(string='Là Ép Film', compute='_compute_stage_flags')

    def _compute_stage_flags(self):
        for rec in self:
            dept_upper = rec.department_id.name.upper() if rec.department_id else ''
            rec.is_kcs_stage = 'KCS' in dept_upper
            rec.is_film_stage = 'ÉP FILM' in dept_upper or 'EP FILM' in dept_upper
    
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

    # Packaging Materials (KCS only)
    x_plastic_belt_qty = fields.Float(string='Dây đai nhựa (cuộn)', tracking=True)
    x_steel_belt_qty = fields.Float(string='Dây đai sắt (cuộn)', tracking=True)
    x_paper_qty = fields.Float(string='Giấy (kg)', tracking=True)
    x_cardboard_qty = fields.Float(string='Bìa (tấm)', tracking=True)

    # Realtime Estimates
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id, readonly=True)
    total_revenue_low = fields.Float(string='Tổng thu nhập (Thấp)', compute='_compute_estimates', store=False)
    total_revenue_high = fields.Float(string='Tổng thu nhập (Cao)', compute='_compute_estimates', store=False)
    total_worked_hours = fields.Float(string='Tổng số công', compute='_compute_estimates', store=False)
    avg_salary_low = fields.Float(string='Lương bình quân (Thấp)', compute='_compute_estimates', store=False)
    avg_salary_high = fields.Float(string='Lương bình quân (Cao)', compute='_compute_estimates', store=False)

    foreign_transfer_ids = fields.Many2many(
        'dl.combined.worker.line',
        compute='_compute_foreign_transfers',
        string='Dữ liệu Chéo (Các tổ khác báo mượn/cho mượn)'
    )

    @api.depends('date', 'production_group_id')
    def _compute_foreign_transfers(self):
        for rec in self:
            if not rec.date or not rec.production_group_id:
                rec.foreign_transfer_ids = False
                continue
                
            group_id = rec.production_group_id.id
            
            # 1. Other team lent someone to us (They are Native, We are Actual)
            domain1 = [
                ('combined_log_id.date', '=', rec.date),
                ('actual_group_id', '=', group_id),
                ('native_group_id', '!=', group_id),
                ('transfer_status', '=', 'lent_out'),
                ('combined_log_id', '!=', rec._origin.id if rec._origin else rec.id)
            ]
            
            # 2. Other team borrowed someone from us (They are Actual, We are Native)
            domain2 = [
                ('combined_log_id.date', '=', rec.date),
                ('native_group_id', '=', group_id),
                ('actual_group_id', '!=', group_id),
                ('transfer_status', '=', 'borrowed_in'),
                ('combined_log_id', '!=', rec._origin.id if rec._origin else rec.id)
            ]
            
            lines1 = self.env['dl.combined.worker.line'].search(domain1)
            lines2 = self.env['dl.combined.worker.line'].search(domain2)
            
            rec.foreign_transfer_ids = (lines1 | lines2).ids

    @api.depends(
        'product_line_ids.quantity', 'product_line_ids.price_low', 'product_line_ids.price_high',
        'worker_line_ids.worked_hours'
    )
    def _compute_estimates(self):
        for rec in self:
            rev_low = sum((p.quantity * p.price_low) for p in rec.product_line_ids)
            rev_high = sum((p.quantity * p.price_high) for p in rec.product_line_ids)
            # Mặc định chỉ tạm tính số công của những người thực té làm ở đây (actual == rec.group)
            hours = sum(w.worked_hours for w in rec.worker_line_ids if w.actual_group_id.id == rec.production_group_id.id)
            
            rec.total_revenue_low = rev_low
            rec.total_revenue_high = rev_high
            rec.total_worked_hours = hours
            
            if hours > 0:
                rec.avg_salary_low = rev_low / hours
                rec.avg_salary_high = rev_high / hours
            else:
                rec.avg_salary_low = 0.0
                rec.avg_salary_high = 0.0

    _sql_constraints = [
        ('group_date_unique', 'unique(production_group_id, date)', 'Tổ này đã có phiếu Cộng Công Lượng cho ngày này!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Mới')) == _('Mới'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dl.combined.log') or '/'
        return super().create(vals_list)

    def unlink(self):
        dates_to_recalc = set()
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("Chỉ có thể xóa các bản ghi ở trạng thái Dự thảo. Vui lòng chọn 'Mở lại dự thảo' trước."))
            
            dates_to_recalc.add(rec.date)
            
            # Xoá bảng chấm công và sản lượng gốc liên quan
            if rec.attendance_id and rec.attendance_id.state == 'draft':
                rec.attendance_id.unlink()
            if rec.production_log_id and rec.production_log_id.state == 'draft':
                rec.production_log_id.unlink()
                
        res = super(CombinedLog, self).unlink()
        
        # Tự động tính lại lương cào bằng cho các ngày bị ảnh hưởng
        if dates_to_recalc:
            pooling_wizard = self.env['dl.pooling.wizard']
            for d in dates_to_recalc:
                wiz = pooling_wizard.create({'date': d, 'calc_type': 'daily'})
                wiz._calculate_for_day(d)
                
        return res

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

            # 2. Load Workers natively
            lines = []
            for employee in self.production_group_id.member_ids:
                lines.append((0, 0, {
                    'employee_id': employee.id,
                    'attendance_type_id': default_type.id if default_type else False,
                    'worked_hours': 1.0,
                    'native_group_id': employee.x_source_group_id.id or self.production_group_id.id,
                    'actual_group_id': self.production_group_id.id
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
            
        unapproved = self.worker_line_ids.filtered(lambda w: w.handshake_status == 'pending')
        warning_action = False
        if unapproved:
            warning_action = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Cảnh báo: Tồn đọng Duyệt Mượn người'),
                    'message': _("Vẫn còn danh sách nhân sự ở trạng thái Chờ Duyệt tổ khác báo sang. Phiếu đã được xác nhận, nhưng những nhân sự mượn này sẽ bị bỏ qua khi Tính lương Cào bằng cho đến khi được duyệt hợp lệ!"),
                    'sticky': True,
                    'type': 'warning',
                }
            }

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
            }) for p in self.product_line_ids],
            'worker_line_ids': [(0, 0, {
                'employee_id': w.employee_id.id,
                'worked_hours': w.worked_hours,
                'native_group_id': w.native_group_id.id,
                'actual_group_id': w.actual_group_id.id,
                'handshake_status': w.handshake_status,
                'transfer_status': w.transfer_status,
            }) for w in self.worker_line_ids],
            'x_plastic_belt_qty': self.x_plastic_belt_qty,
            'x_steel_belt_qty': self.x_steel_belt_qty,
            'x_paper_qty': self.x_paper_qty,
            'x_cardboard_qty': self.x_cardboard_qty,
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
        
        if warning_action:
            return warning_action
        return True

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
    
    price_low = fields.Float(string='ĐG cũ', compute='_compute_prices', store=True)
    price_high = fields.Float(string='ĐG mới', compute='_compute_prices', store=True)

    @api.depends('combined_log_id.date', 'product_id', 'combined_log_id.department_id')
    def _compute_prices(self):
        for rec in self:
            rec.price_low = 0.0
            rec.price_high = 0.0
            log = rec.combined_log_id
            if not log or not log.date or not log.department_id or not rec.product_id:
                continue
                
            # Tra cứu bảng giá công đoạn bình thường (Cào bằng)
            res = self.env['dl.piece.rate.pricelist']._get_active_price(
                log.date, 
                log.department_id, 
                rec.product_id
            )
            rec.price_low = res.get('price_low', 0.0)
            rec.price_high = res.get('price_high', 0.0)

class CombinedWorkerLine(models.Model):
    _name = 'dl.combined.worker.line'
    _description = 'Chi tiết nhân sự cộng dồn'
    _order = 'id'

    combined_log_id = fields.Many2one('dl.combined.log', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True)
    attendance_type_id = fields.Many2one('dl.attendance.type', string='Loại công', required=True)
    worked_hours = fields.Float(string='Số công', digits=(16, 1), store=True, compute='_compute_worked_hours')

    @api.depends('attendance_type_id')
    def _compute_worked_hours(self):
        for line in self:
            if line.attendance_type_id:
                line.worked_hours = line.attendance_type_id.work_value
            else:
                line.worked_hours = 0.0

    @api.onchange('attendance_type_id')
    def _onchange_attendance_type_id(self):
        if self.attendance_type_id:
            self.worked_hours = self.attendance_type_id.work_value
        else:
            self.worked_hours = 0.0
    
    native_group_id = fields.Many2one('dl.production.group', string='Tổ biên chế', related='employee_id.x_source_group_id', store=True)
    actual_group_id = fields.Many2one('dl.production.group', string='Tổ thực tế làm việc')

    transfer_status = fields.Selection([
        ('native', 'Biên chế'),
        ('lent_out', 'Cho mượn'),
        ('borrowed_in', 'Mượn người')
    ], string='Phân loại', compute='_compute_transfer_status', store=True)

    handshake_status = fields.Selection([
        ('n/a', '-'),
        ('pending', 'Chờ duyệt'),
        ('confirmed', 'Đã duyệt'),
        ('rejected', 'Từ chối')
    ], string='Duyệt', default='n/a')
    
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            # Native is automatically linked by related field when creating
            if not self.actual_group_id:
                # Default to Log Group
                self.actual_group_id = self.combined_log_id.production_group_id.id or self.employee_id.x_source_group_id.id

    @api.depends('native_group_id', 'actual_group_id', 'combined_log_id.production_group_id')
    def _compute_transfer_status(self):
        for rec in self:
            log_group = rec.combined_log_id.production_group_id
            if rec.native_group_id and rec.actual_group_id:
                if rec.native_group_id == rec.actual_group_id:
                    rec.transfer_status = 'native'
                    if rec.handshake_status != 'n/a':
                        rec.handshake_status = 'n/a'
                elif rec.native_group_id == log_group:
                    # Log owner is lending out worker
                    rec.transfer_status = 'lent_out'
                    if rec.handshake_status == 'n/a':
                        rec.handshake_status = 'pending'
                elif rec.actual_group_id == log_group:
                    # Log owner is borrowing worker in
                    rec.transfer_status = 'borrowed_in'
                    if rec.handshake_status == 'n/a':
                        rec.handshake_status = 'pending'
                else:
                    rec.transfer_status = 'native'
            else:
                rec.transfer_status = 'native'
                
    def action_handshake_approve(self):
        for rec in self:
            rec.handshake_status = 'confirmed'

    def action_handshake_reject(self):
        for rec in self:
            rec.handshake_status = 'rejected'
