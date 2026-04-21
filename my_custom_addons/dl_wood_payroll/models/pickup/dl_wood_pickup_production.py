# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class WoodPickupProduction(models.Model):
    _name = 'dl.wood.pickup.production'
    _description = 'Ghi nhận Sản lượng Nhặt ván'
    _order = 'date desc, id desc'

    @api.model
    def _get_default_date(self):
        """Lấy ngày cuối cùng có ghi nhận trong tháng hiện tại, mặc định mùng 1"""
        today = fields.Date.context_today(self)
        first_day = today.replace(day=1)
        last_record = self.search([
            ('date', '>=', first_day),
            ('date', '<=', today)
        ], order='date desc', limit=1)
        if last_record:
            return last_record.date
        return first_day

    name = fields.Char(string='Số phiếu', required=True, copy=False, readonly=True, default=lambda self: _('Mới'))
    date = fields.Date(string='Ngày ghi nhận', required=True, default=_get_default_date)
    
    x_group_id = fields.Many2one('dl.production.group', string='Tổ sản xuất', required=True,
                                domain=[('department_id.x_is_nhat_van', '=', True)])
    
    attendance_ids = fields.One2many('dl.wood.pickup.production.attendance', 'production_id', string='Chi tiết chấm công')
    
    employee_ids = fields.Many2many('hr.employee', string='Nhân viên tham gia', 
                                    compute='_compute_employee_ids', store=True)

    @api.depends('attendance_ids.employee_id')
    def _compute_employee_ids(self):
        for rec in self:
            rec.employee_ids = rec.attendance_ids.mapped('employee_id')
    
    pricelist_id = fields.Many2one('dl.wood.pickup.pricelist', string='Bảng giá áp dụng', 
                                  compute='_compute_pricelist', store=True, readonly=True)
    
    line_ids = fields.One2many('dl.wood.pickup.production.line', 'production_id', string='Chi tiết sản lượng')
    # Doanh thu tổ & So sánh
    # Phân tích chi tiết so sánh
    total_wage = fields.Float(string='Tổng doanh thu Tổ', compute='_compute_total_revenue', store=True)
    
    total_amount_old = fields.Float(string='Tổng tiền (ĐG Cũ)', compute='_compute_total_revenue', store=True)
    amount_old_base = fields.Float(string='Tiền Base (Cũ)', compute='_compute_total_revenue', store=True)
    amount_old_bonus = fields.Float(string='Tiền Bonus (Cũ)', compute='_compute_total_revenue', store=True)
    display_amount_old = fields.Char(string='Phân tích ĐG Cũ', compute='_compute_total_revenue', store=True)
    
    total_amount_new = fields.Float(string='Tổng tiền (ĐG Mới)', compute='_compute_total_revenue', store=True)
    amount_new_base = fields.Float(string='Tiền Base (Mới)', compute='_compute_total_revenue', store=True)
    amount_new_bonus = fields.Float(string='Tiền Bonus (Mới)', compute='_compute_total_revenue', store=True)
    display_amount_new = fields.Char(string='Phân tích ĐG Mới', compute='_compute_total_revenue', store=True)

    avg_wage_old = fields.Float(string='Bình quân (ĐG Cũ)', compute='_compute_total_revenue', store=True)
    avg_wage_new = fields.Float(string='Bình quân (ĐG Mới)', compute='_compute_total_revenue', store=True)

    num_participants = fields.Integer(string='Số người tham gia', compute='_compute_total_revenue', store=True)
    total_attendance_weight = fields.Float(string='Tổng trọng số công', compute='_compute_total_revenue', store=True)

    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('confirmed', 'Xác nhận'),
        ('settled', 'Đã quyết toán')
    ], string='Trạng thái', default='draft', required=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Mới')) == _('Mới'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dl.wood.pickup.production') or _('Mới')
        return super().create(vals_list)

    @api.depends('date')
    def _compute_pricelist(self):
        for rec in self:
            pricelist = self.env['dl.wood.pickup.pricelist'].search([
                ('state', '=', 'active')
            ], limit=1)
            rec.pricelist_id = pricelist

    @api.depends('line_ids.amount_total', 'line_ids.quantity', 'line_ids.price_old', 'line_ids.price_new', 
                 'line_ids.price_bonus_extra', 'attendance_ids.attendance_value')
    def _compute_total_revenue(self):
        for rec in self:
            actual_total = sum(rec.line_ids.mapped('amount_total'))
            total_att = sum(rec.attendance_ids.mapped('attendance_value')) or 1.0
            threshold = total_att * 280.0
            
            # 1. Simulating OLD comparison
            old_base_total, old_bonus_total = 0.0, 0.0
            lines_old = sorted(rec.line_ids, key=lambda l: l.price_old if l.price_old > 0 else (l.price_new or 999999))
            rem_old = threshold
            for line in lines_old:
                p_base = line.price_old if (line.price_old > 0) else (line.price_new)
                qty_base = min(line.quantity, rem_old)
                qty_bonus = line.quantity - qty_base
                old_base_total += qty_base * p_base
                old_bonus_total += qty_bonus * (p_base + line.price_bonus_extra)
                rem_old = max(0.0, rem_old - qty_base)
            
            # 2. Simulating NEW comparison
            new_base_total, new_bonus_total = 0.0, 0.0
            lines_new = sorted(rec.line_ids, key=lambda l: l.price_new)
            rem_new = threshold
            for line in lines_new:
                p_base = line.price_new
                qty_base = min(line.quantity, rem_new)
                qty_bonus = line.quantity - qty_base
                new_base_total += qty_base * p_base
                new_bonus_total += qty_bonus * (p_base + line.price_bonus_extra)
                rem_new = max(0.0, rem_new - qty_base)

            rec.total_wage = actual_total
            
            # Old Result
            rec.amount_old_base = old_base_total
            rec.amount_old_bonus = old_bonus_total
            rec.total_amount_old = old_base_total + old_bonus_total
            rec.display_amount_old = "{:,.0f} = {:,.0f} + {:,.0f}".format(rec.total_amount_old, old_base_total, old_bonus_total)
            rec.avg_wage_old = rec.total_amount_old / total_att
            
            # New Result
            rec.amount_new_base = new_base_total
            rec.amount_new_bonus = new_bonus_total
            rec.total_amount_new = new_base_total + new_bonus_total
            rec.display_amount_new = "{:,.0f} = {:,.0f} + {:,.0f}".format(rec.total_amount_new, new_base_total, new_bonus_total)
            rec.avg_wage_new = rec.total_amount_new / total_att

            # Thống kê nhân sự cho Tree View
            rec.num_participants = len(rec.attendance_ids)
            rec.total_attendance_weight = sum(rec.attendance_ids.mapped('attendance_value'))

    @api.onchange('x_group_id', 'date')
    def _onchange_x_group_id(self):
        if self.x_group_id:
            # 1. Load nhân viên và mặc định công N
            type_n = self.env['dl.attendance.type'].search([('code', '=', 'N')], limit=1)
            current_employees = self.attendance_ids.mapped('employee_id')
            new_lines = []
            for emp in self.x_group_id.x_employee_ids:
                if emp not in current_employees:
                    new_lines.append((0, 0, {
                        'employee_id': emp.id,
                        'attendance_type_id': type_n.id if type_n else False,
                        'attendance_value': type_n.work_value if type_n else 1.0
                    }))
            if new_lines:
                self.attendance_ids = new_lines
            
            pricelist = self.env['dl.wood.pickup.pricelist'].search([
                ('state', '=', 'active')
            ], limit=1)
            if pricelist:
                self.pricelist_id = pricelist
            if not self.line_ids:
                self.action_load_products()

    def action_load_products(self):
        self.ensure_one()
        existing_products = self.line_ids.mapped('product_id')
        products = self.env['product.product'].search([
            ('x_production_stage_ids.x_is_nhat_van', '=', True)
        ])
        lines = []
        for product in products:
            if product and product.id and product not in existing_products:
                lines.append((0, 0, {
                    'product_id': product.id,
                    'quantity': 0.0
                }))
        if lines:
            self.line_ids = lines

    def action_confirm(self):
        for rec in self:
            rec.write({'state': 'confirmed'})
            rec._generate_attendance()

    def action_draft(self):
        for rec in self:
            # Xóa các bản ghi điểm danh đã được tạo tự động từ phiếu này
            attendances = self.env['hr.attendance'].search([
                ('x_wood_pickup_id', '=', rec.id)
            ])
            if attendances:
                attendances.unlink()
            rec.write({'state': 'draft'})

    def _generate_attendance(self):
        Attendance = self.env['hr.attendance']
        for rec in self:
            for line in rec.attendance_ids:
                if line.attendance_value > 0:
                    check_in = fields.Datetime.to_datetime(rec.date).replace(hour=8, minute=0)
                    check_out = fields.Datetime.to_datetime(rec.date).replace(hour=18, minute=0)
                    exists = Attendance.search([
                        ('employee_id', '=', line.employee_id.id),
                        ('check_in', '>=', check_in.replace(hour=0, minute=0, second=0)),
                        ('check_in', '<=', check_in.replace(hour=23, minute=59, second=59))
                    ], limit=1)
                    if not exists:
                        Attendance.create({
                            'employee_id': line.employee_id.id,
                            'check_in': check_in,
                            'check_out': check_out,
                            'x_wood_pickup_id': rec.id,
                        })

class WoodPickupProductionAttendance(models.Model):
    _name = 'dl.wood.pickup.production.attendance'
    _description = 'Chi tiết chấm công & Lương Nhặt ván'

    production_id = fields.Many2one('dl.wood.pickup.production', string='Phiếu sản lượng', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True)
    
    # Kết nối hệ thống Loại công (Mới)
    attendance_type_id = fields.Many2one('dl.attendance.type', string='Loại công', required=True)
    attendance_value = fields.Float(string='Số công (Trọng số)', default=1.0)
    
    wage_amount = fields.Float(string='Lương nhận được', compute='_compute_wage', store=True,
                              help="Công thức: (Tổng doanh thu Tổ / Tổng trọng số công cả tổ) * Trọng số công cá nhân")
    is_qualified = fields.Boolean(string='Đạt ĐK giá mới', default=False, help="Tự động cập nhật khi quyết toán tháng dựa trên bảo hiểm và số công.")
    month_total_weight = fields.Float(string='Tổng công tháng', help="Tổng trọng số công tích lũy trong tháng này.")

    @api.onchange('attendance_type_id')
    def _onchange_attendance_type_id(self):
        """Tự động cập nhật trọng số khi chọn loại công"""
        if self.attendance_type_id:
            self.attendance_value = self.attendance_type_id.work_value

    @api.depends('production_id.total_wage', 'production_id.total_attendance_weight', 'attendance_value',
                 'is_qualified', 'production_id.line_ids.amount_total', 'production_id.line_ids.qty_base', 'production_id.line_ids.qty_bonus')
    def _compute_wage(self):
        for rec in self:
            total_weight = rec.production_id.total_attendance_weight or 1.0
            ratio = rec.attendance_value / total_weight
            
            individual_wage = 0.0
            for line in rec.production_id.line_ids:
                # Quyết định đơn giá dựa trên trạng thái qualify của cá nhân
                p_base = line.price_new if rec.is_qualified else line.price_old
                # Nếu sản phẩm hoàn toàn mới (ko có giá cũ) thì mặc định dùng giá mới
                if not p_base and line.price_new:
                    p_base = line.price_new
                
                p_bonus = p_base + line.price_bonus_extra
                
                # Chia phần sản lượng của cá nhân dựa trên tỷ trọng công
                ind_qty_base = line.qty_base * ratio
                ind_qty_bonus = line.qty_bonus * ratio
                
                individual_wage += (ind_qty_base * p_base) + (ind_qty_bonus * p_bonus)
                
            rec.wage_amount = individual_wage

class WoodPickupProductionLine(models.Model):
    _name = 'dl.wood.pickup.production.line'
    _description = 'Chi tiết sản lượng Nhặt ván line'

    production_id = fields.Many2one('dl.wood.pickup.production', string='Phiếu sản lượng', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Sản phẩm', required=True)
    quantity = fields.Float(string='Sản lượng', default=0.0)
    
    price_new = fields.Float(string='Giá mới', compute='_compute_prices', store=True)
    price_old = fields.Float(string='Giá cũ', compute='_compute_prices', store=True)
    price_bonus_extra = fields.Float(string='Giá thưởng thêm', compute='_compute_prices', store=True)
    
    qty_base = fields.Float(string='SL Giá Base', compute='_compute_distributions', store=True)
    qty_bonus = fields.Float(string='SL Giá Bonus', compute='_compute_distributions', store=True)
    amount_total = fields.Float(string='Thành tiền', compute='_compute_distributions', store=True)

    @api.depends('product_id', 'production_id.pricelist_id')
    def _compute_prices(self):
        for rec in self:
            p_old, p_new, p_extra = 0.0, 0.0, 0.0
            if rec.production_id.pricelist_id:
                p_conf = rec.production_id.pricelist_id.line_ids.filtered(lambda l: l.product_id == rec.product_id)
                if p_conf:
                    p_old, p_new, p_extra = p_conf[0].price_old, p_conf[0].price_new, p_conf[0].price_bonus_extra
            rec.price_old = p_old
            rec.price_new = p_new
            rec.price_bonus_extra = p_extra

    @api.depends('quantity', 'production_id.attendance_ids.attendance_value', 'production_id.pricelist_id', 'production_id.line_ids.quantity',
                 'price_old', 'price_new', 'price_bonus_extra')
    def _compute_distributions(self):
        productions = self.mapped('production_id')
        for prod in productions:
            lines = prod.line_ids
            total_att_val = sum(prod.attendance_ids.mapped('attendance_value')) or 1.0
            total_threshold = total_att_val * 280.0
            
            priced_lines = []
            for line in lines:
                p_old = line.price_old
                p_new = line.price_new
                p_extra = line.price_bonus_extra
                
                eff_base = p_new if (p_new > 0 and p_old == 0) else p_old
                priced_lines.append({
                    'line': line, 
                    'p_base': eff_base, 
                    'p_extra': p_extra, 
                    'qty': line.quantity
                })
            
            priced_lines.sort(key=lambda x: x['p_base'])
            
            rem_base = total_threshold
            for item in priced_lines:
                line = item['line']
                line_base = min(item['qty'], rem_base)
                line_bonus = item['qty'] - line_base
                line.qty_base, line.qty_bonus = line_base, line_bonus
                line.amount_total = (line_base * item['p_base']) + (line_bonus * (item['p_base'] + item['p_extra']))
                rem_base = max(0.0, rem_base - line_base)
