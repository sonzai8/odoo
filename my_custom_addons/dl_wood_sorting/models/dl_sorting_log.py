# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SortingLog(models.Model):
    _name = 'dl.sorting.log'
    _description = 'Phiếu Nghiệm Thu Nhặt Ván'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Số phiếu', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    date = fields.Date(string='Ngày nghiệm thu', required=True, default=fields.Date.context_today)
    line_ids = fields.One2many('dl.sorting.log.line', 'log_id', string='Chi tiết nhân viên')
    
    total_qty_17 = fields.Float(string='Tổng bó 1.7 ly', compute='_compute_totals', store=True)
    total_qty_20 = fields.Float(string='Tổng bó 2.0 ly', compute='_compute_totals', store=True)

    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('confirmed', 'Xác nhận')
    ], string='Trạng thái', default='draft', tracking=True)

    @api.depends('line_ids.qty_17', 'line_ids.qty_20')
    def _compute_totals(self):
        for record in self:
            record.total_qty_17 = sum(line.qty_17 for line in record.line_ids)
            record.total_qty_20 = sum(line.qty_20 for line in record.line_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dl.sorting.log') or _('New')
        return super().create(vals_list)

    def action_confirm(self):
        for record in self:
            if not record.line_ids:
                raise ValidationError(_("Vui lòng thêm ít nhất một nhân viên."))
            record.state = 'confirmed'

    def action_draft(self):
        self.write({'state': 'draft'})

class SortingLogLine(models.Model):
    _name = 'dl.sorting.log.line'
    _description = 'Chi tiết sản lượng Nhặt Ván'

    log_id = fields.Many2one('dl.sorting.log', string='Phiếu', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True)
    attendance_type_id = fields.Many2one('dl.attendance.type', string='Loại công', 
                                        required=True, 
                                        default=lambda self: self.env['dl.attendance.type'].search([], limit=1).id)
    
    qty_17 = fields.Float(string='Bó 1.7 ly', default=0.0)
    qty_20 = fields.Float(string='Bó 2.0 ly', default=0.0)

    work_value = fields.Float(string='Giá trị công', compute='_compute_calculations', store=True)
    is_new_price = fields.Boolean(string='Hưởng giá Mới', compute='_compute_calculations', store=True)
    amount = fields.Monetary(string='Thành tiền', compute='_compute_calculations', store=True)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)

    @api.depends('qty_17', 'qty_20', 'attendance_type_id', 'employee_id.x_has_insurance')
    def _compute_calculations(self):
        pricelist = self.env['dl.sorting.pricelist'].get_latest_price()
        
        for line in self:
            work_val = line.attendance_type_id.work_value
            line.work_value = work_val
            
            # Logic hưởng giá mới: (Có BHXH) VÀ (Công >= 1.0)
            line.is_new_price = line.employee_id.x_has_insurance and work_val >= 1.0
            
            # 1. Định mức cá nhân
            threshold = 280.0 * work_val
            
            # 2. Phân bổ Base/Bonus (Ưu tiên 1.7 ly trước)
            qty_17_base = min(line.qty_17, threshold)
            remaining_t = max(0, threshold - qty_17_base)
            
            qty_20_base = min(line.qty_20, remaining_t)
            
            qty_17_bonus = max(0, line.qty_17 - qty_17_base)
            qty_20_bonus = max(0, line.qty_20 - qty_20_base)

            if not pricelist:
                line.amount = 0
                continue

            # 3. Tính cả 2 kịch bản lương
            # Scenario: New
            total_new = (qty_17_base * pricelist.price_17_base_new) + \
                        (qty_20_base * pricelist.price_20_base_new) + \
                        (qty_17_bonus * pricelist.price_17_bonus_new) + \
                        (qty_20_bonus * pricelist.price_20_bonus_new)
            
            # Scenario: Old
            total_old = (qty_17_base * pricelist.price_17_base_old) + \
                        (qty_20_base * pricelist.price_20_base_old) + \
                        (qty_17_bonus * pricelist.price_17_bonus_old) + \
                        (qty_20_bonus * pricelist.price_20_bonus_old)

            # 4. Xác định lương thực nhận
            if line.is_new_price:
                line.amount = total_new
            else:
                line.amount = total_old
