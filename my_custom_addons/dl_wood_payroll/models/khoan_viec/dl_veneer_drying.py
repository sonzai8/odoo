# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class DryingPricelist(models.Model):
    _name = 'dl.drying.pricelist'
    _description = 'Bảng giá Phơi ván'
    _order = 'veneer_type, thickness, quality'

    name = fields.Char(string='Tên bảng giá', required=True)
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
        ('type_thick_quality_unique', 'unique(veneer_type, thickness, quality)', 'Đã tồn tại đơn giá cho loại ván này!')
    ]

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.get_veneer_type_desc()} - {rec.thickness} ly - {rec.quality}"
            result.append((rec.id, name))
        return result

    def get_veneer_type_desc(self):
        return dict(self._fields['veneer_type'].selection).get(self.veneer_type)

class VeneerDryingLog(models.Model):
    _name = 'dl.veneer.drying.log'
    _description = 'Phiếu Nghiệm Thu Phơi Ván'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    date = fields.Date(string='Ngày nghiệm thu', default=fields.Date.today(), required=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True, tracking=True)
    
    veneer_type = fields.Selection([
        ('am', 'Ván Ẩm'),
        ('boc', 'Ván Bóc')
    ], string='Loại ván', required=True, tracking=True)
    thickness = fields.Selection([
        ('1.7', '1.7 ly'),
        ('2.0', '2.0 ly')
    ], string='Độ dày', required=True, tracking=True)
    quality = fields.Selection([
        ('A', 'Loại A'),
        ('BC', 'Loại BC')
    ], string='Chất lượng', required=True, tracking=True)
    
    quantity = fields.Integer(string='Số lượng', required=True, tracking=True)
    unit_price = fields.Float(string='Đơn giá', compute='_compute_unit_price', store=True, readonly=False)
    
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)
    total_amount = fields.Monetary(string='Thành tiền', compute='_compute_total_amount', store=True, currency_field='currency_id')
    
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('confirmed', 'Đã xác nhận')
    ], string='Trạng thái', default='confirmed', tracking=True) # Mặc định confirmed để nhập liệu nhanh

    @api.depends('veneer_type', 'thickness', 'quality')
    def _compute_unit_price(self):
        for rec in self:
            if rec.veneer_type and rec.thickness and rec.quality:
                pricelist = self.env['dl.drying.pricelist'].search([
                    ('veneer_type', '=', rec.veneer_type),
                    ('thickness', '=', rec.thickness),
                    ('quality', '=', rec.quality)
                ], limit=1)
                rec.unit_price = pricelist.unit_price if pricelist else 0.0
            else:
                rec.unit_price = 0.0

    @api.depends('quantity', 'unit_price')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.quantity * rec.unit_price

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.state == 'confirmed':
                self._auto_create_attendance(rec)
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'state' in vals and vals['state'] == 'confirmed':
            for rec in self:
                self._auto_create_attendance(rec)
        return res

    def _auto_create_attendance(self, rec):
        """Tự động sinh công nếu nhân viên chưa có chấm công trong ngày"""
        AttendanceLine = self.env['dl.daily.attendance.line']
        Attendance = self.env['dl.daily.attendance']
        
        # Lấy loại công mặc định (N)
        default_type = self.env.ref('dl_wood_payroll.attendance_type_n', False)
        if not default_type:
            default_type = self.env['dl.attendance.type'].search([('code', '=', 'N')], limit=1)

        # Kiểm tra xem nhân viên đã có công trong ngày chưa
        exists = AttendanceLine.search_count([
            ('employee_id', '=', rec.employee_id.id),
            ('date', '=', rec.date),
            ('actual_work', '>=', 0.1)
        ])
        if not exists:
            # Tìm hoặc tạo phiếu chấm công cho tổ gốc của nhân viên
            group = rec.employee_id.x_source_group_id
            if not group:
                return
            
            att = Attendance.search([
                ('production_group_id', '=', group.id),
                ('date', '=', rec.date)
            ], limit=1)
            
            if not att:
                att = Attendance.create({
                    'production_group_id': group.id,
                    'date': rec.date,
                    'state': 'confirmed'
                })
            
            AttendanceLine.create({
                'attendance_id': att.id,
                'employee_id': rec.employee_id.id,
                'attendance_type_id': default_type.id if default_type else False,
            })

    def action_confirm(self):
        for rec in self:
            rec.write({'state': 'confirmed'})

    def action_draft(self):
        self.write({'state': 'draft'})
