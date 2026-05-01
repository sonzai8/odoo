# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class DryingPricelist(models.Model):
    _name = 'dl.drying.pricelist'
    _inherit = ['mail.thread']
    _description = 'Bảng giá Phơi ván'
    _order = 'year desc, month desc'

    name = fields.Char(string='Tên bảng giá', compute='_compute_name', store=True)
    month = fields.Integer(string='Tháng', default=lambda self: fields.Date.today().month, required=True)
    year = fields.Integer(string='Năm', default=lambda self: fields.Date.today().year, required=True)
    state = fields.Selection([
        ('draft', 'Mới'),
        ('confirmed', 'Xác nhận')
    ], string='Trạng thái', default='draft', copy=False, tracking=True)

    line_ids = fields.One2many('dl.drying.pricelist.line', 'pricelist_id', string='Chi tiết đơn giá')

    _sql_constraints = [
        ('month_year_unique', 'unique(month, year)', 'Bảng giá cho tháng/năm này đã tồn tại!')
    ]

    @api.depends('month', 'year')
    def _compute_name(self):
        for rec in self:
            rec.name = "GIA-PHOI-%02d-%d" % (rec.month, rec.year)

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_clone_pricelist(self):
        self.ensure_one()
        if self.state == 'confirmed':
            raise ValidationError(_("Không thể clone vào bảng giá đã xác nhận."))
        
        prev_month = self.month - 1
        prev_year = self.year
        if prev_month == 0:
            prev_month = 12
            prev_year -= 1
        
        last_pricelist = self.search([
            ('month', '=', prev_month),
            ('year', '=', prev_year),
            ('state', '=', 'confirmed')
        ], limit=1)
        
        if not last_pricelist:
            raise ValidationError(_("Không tìm thấy bảng giá đã xác nhận của tháng %s/%s để sao chép.") % (prev_month, prev_year))
        
        self.line_ids.unlink()
        
        vals_list = []
        for line in last_pricelist.line_ids:
            vals_list.append({
                'pricelist_id': self.id,
                'veneer_type': line.veneer_type,
                'thickness': line.thickness,
                'quality': line.quality,
                'unit_price': line.unit_price,
            })
        
        if vals_list:
            self.env['dl.drying.pricelist.line'].create(vals_list)
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành công'),
                'message': _('Đã sao chép %s dòng từ bảng giá tháng %s/%s.') % (len(vals_list), prev_month, prev_year),
                'sticky': False,
            }
        }

    @api.model
    def _get_active_price(self, date, veneer_type, thickness, quality):
        if not date or not veneer_type or not thickness or not quality:
            return 0.0
        
        pricelist = self.search([
            ('month', '=', date.month),
            ('year', '=', date.year),
            ('state', '=', 'confirmed')
        ], limit=1)
        
        if not pricelist:
            return 0.0
        
        line = self.env['dl.drying.pricelist.line'].search([
            ('pricelist_id', '=', pricelist.id),
            ('veneer_type', '=', veneer_type),
            ('thickness', '=', thickness),
            ('quality', '=', quality)
        ], limit=1)
        return line.unit_price if line else 0.0

class DryingPricelistLine(models.Model):
    _name = 'dl.drying.pricelist.line'
    _description = 'Chi tiết bảng giá phơi ván'
    _order = 'veneer_type, thickness, quality'

    pricelist_id = fields.Many2one('dl.drying.pricelist', string='Bảng giá', ondelete='cascade')
    veneer_type = fields.Selection([
        ('am', 'Ván Ẩm'),
        ('boc', 'Ván Bóc')
    ], string='Loại ván', required=True)
    thickness = fields.Selection([
        ('1.7', '1.7 ly'),
        ('2.0', '2.0 ly')
    ], string='Độ dày', required=True)
    quality = fields.Selection([
        ('A', 'Loại A'),
        ('BC', 'Loại BC')
    ], string='Chất lượng', required=True)
    unit_price = fields.Float(string='Đơn giá', required=True)

    _sql_constraints = [
        ('pricelist_line_unique', 'unique(pricelist_id, veneer_type, thickness, quality)', 'Đã tồn tại đơn giá cho tổ hợp này trong bảng giá!')
    ]

class VeneerDryingLog(models.Model):
    _name = 'dl.veneer.drying.log'
    _description = 'Phiếu Nghiệm Thu Phơi Ván'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    date = fields.Date(string='Ngày nghiệm thu', default=fields.Date.today(), required=True, tracking=True)
    production_group_id = fields.Many2one('dl.production.group', string='Tổ sản xuất thực hiện', required=True, tracking=True)
    
    line_ids = fields.One2many('dl.veneer.drying.line', 'log_id', string='Chi tiết sản lượng', copy=True)
    matrix_line_ids = fields.One2many('dl.veneer.drying.matrix.line', 'log_id', string='Ma trận sản lượng', copy=True)
    
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('confirmed', 'Đã xác nhận')
    ], string='Trạng thái', default='draft', tracking=True)

    @api.onchange('production_group_id', 'date')
    def _onchange_production_group_id(self):
        if self.production_group_id and self.date:
            matrix_lines = []
            for employee in self.production_group_id.member_ids:
                matrix_lines.append((0, 0, {
                    'employee_id': employee.id,
                }))
            self.matrix_line_ids = [(5, 0, 0)] + matrix_lines

    def action_confirm(self):
        for rec in self:
            if not rec.matrix_line_ids:
                raise ValidationError(_("Vui lòng nhập sản lượng vào ma trận trước khi xác nhận."))
            
            # Đồng bộ dữ liệu từ Ma trận sang Line chuẩn trước khi chốt
            rec._sync_matrix_to_lines()
            
            # Kiểm tra đơn giá
            if any(line.unit_price <= 0 for line in rec.line_ids):
                raise ValidationError(_("Một số sản phẩm chưa có đơn giá trong bảng giá tháng này. Vui lòng kiểm tra và xác nhận Bảng giá trước."))
            
            rec.write({'state': 'confirmed'})
            for line in rec.line_ids:
                if line.quantity > 0:
                    self._auto_create_attendance(line)

    def _sync_matrix_to_lines(self):
        """Chuyển đổi dữ liệu từ Matrix sang Line chuẩn"""
        self.line_ids.unlink()
        line_vals = []
        
        # Ánh xạ giữa trường trên Matrix và Quy cách ván
        mapping = [
            ('qty_am_17_a', 'am', '1.7', 'A'),
            ('qty_am_17_bc', 'am', '1.7', 'BC'),
            ('qty_am_20_a', 'am', '2.0', 'A'),
            ('qty_am_20_bc', 'am', '2.0', 'BC'),
            ('qty_boc_17_a', 'boc', '1.7', 'A'),
            ('qty_boc_17_bc', 'boc', '1.7', 'BC'),
            ('qty_boc_20_a', 'boc', '2.0', 'A'),
            ('qty_boc_20_bc', 'boc', '2.0', 'BC'),
        ]
        
        for m_line in self.matrix_line_ids:
            for field, v_type, thickness, quality in mapping:
                qty = getattr(m_line, field)
                if qty > 0:
                    line_vals.append((0, 0, {
                        'log_id': self.id,
                        'employee_id': m_line.employee_id.id,
                        'veneer_type': v_type,
                        'thickness': thickness,
                        'quality': quality,
                        'quantity': qty,
                    }))
        
        if line_vals:
            self.line_ids = line_vals

    def action_draft(self):
        self.write({'state': 'draft'})

    def _auto_create_attendance(self, line):
        """Tự động sinh công nếu nhân viên chưa có chấm công trong ngày"""
        AttendanceLine = self.env['dl.daily.attendance.line']
        Attendance = self.env['dl.daily.attendance']
        
        default_type = self.env.ref('dl_wood_payroll.attendance_type_n', False)
        if not default_type:
            default_type = self.env['dl.attendance.type'].search([('code', '=', 'N')], limit=1)

        exists = AttendanceLine.search_count([
            ('employee_id', '=', line.employee_id.id),
            ('date', '=', line.log_id.date),
            ('actual_work', '>=', 0.1)
        ])
        if not exists:
            group = line.employee_id.x_source_group_id
            if not group: return
            
            att = Attendance.search([
                ('production_group_id', '=', group.id),
                ('date', '=', line.log_id.date)
            ], limit=1)
            
            if not att:
                att = Attendance.create({
                    'production_group_id': group.id,
                    'date': line.log_id.date,
                    'state': 'confirmed'
                })
            
            AttendanceLine.create({
                'attendance_id': att.id,
                'employee_id': line.employee_id.id,
                'attendance_type_id': default_type.id if default_type else False,
            })

class VeneerDryingLine(models.Model):
    _name = 'dl.veneer.drying.line'
    _description = 'Chi tiết nghiệm thu phơi ván'
    _order = 'employee_id, veneer_type, thickness, quality'

    log_id = fields.Many2one('dl.veneer.drying.log', string='Phiếu nghiệm thu', ondelete='cascade')
    date = fields.Date(related='log_id.date', store=True, index=True)
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True)
    x_source_group_id = fields.Many2one('dl.production.group', related='employee_id.x_source_group_id', string='Tổ biên chế', store=True)
    
    veneer_type = fields.Selection([
        ('am', 'Ván Ẩm'),
        ('boc', 'Ván Bóc')
    ], string='Loại ván', required=True)
    thickness = fields.Selection([
        ('1.7', '1.7 ly'),
        ('2.0', '2.0 ly')
    ], string='Độ dày', required=True)
    quality = fields.Selection([
        ('A', 'Loại A'),
        ('BC', 'Loại BC')
    ], string='Chất lượng', required=True)
    
    quantity = fields.Integer(string='Số lượng', required=True)
    unit_price = fields.Float(string='Đơn giá', compute='_compute_unit_price', store=True, readonly=False)
    
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)
    total_amount = fields.Monetary(string='Thành tiền', compute='_compute_total_amount', store=True, currency_field='currency_id')

    @api.depends('date', 'veneer_type', 'thickness', 'quality')
    def _compute_unit_price(self):
        for rec in self:
            if rec.date and rec.veneer_type and rec.thickness and rec.quality:
                rec.unit_price = self.env['dl.drying.pricelist']._get_active_price(
                    rec.date, rec.veneer_type, rec.thickness, rec.quality
                )
            else:
                rec.unit_price = 0.0

    @api.depends('quantity', 'unit_price')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.quantity * rec.unit_price

class VeneerDryingMatrixLine(models.Model):
    _name = 'dl.veneer.drying.matrix.line'
    _description = 'Ma trận sản lượng phơi ván'
    _order = 'employee_id'

    log_id = fields.Many2one('dl.veneer.drying.log', string='Phiếu nghiệm thu', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True)
    
    # 8 Cột sản lượng cho các tổ hợp quy cách ván
    qty_am_17_a = fields.Integer(string='Ván Ẩm 1.7 A')
    qty_am_17_bc = fields.Integer(string='Ván Ẩm 1.7 BC')
    qty_am_20_a = fields.Integer(string='Ván Ẩm 2.0 A')
    qty_am_20_bc = fields.Integer(string='Ván Ẩm 2.0 BC')
    
    qty_boc_17_a = fields.Integer(string='Ván Bóc 1.7 A')
    qty_boc_17_bc = fields.Integer(string='Ván Bóc 1.7 BC')
    qty_boc_20_a = fields.Integer(string='Ván Bóc 2.0 A')
    qty_boc_20_bc = fields.Integer(string='Ván Bóc 2.0 BC')
