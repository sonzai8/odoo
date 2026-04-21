# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class WoodPickupPricelist(models.Model):
    _name = 'dl.wood.pickup.pricelist'
    _description = 'Bảng giá Nhặt ván'
    _order = 'month desc'

    name = fields.Char(string='Tên bảng giá', compute='_compute_name', store=True)
    month = fields.Date(string='Tháng/Năm', required=True, default=fields.Date.context_today)
    min_workdays = fields.Float(string='Số công tối thiểu hưởng giá mới', default=20.0)
    
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('active', 'Đang áp dụng'),
        ('expired', 'Hết hạn')
    ], string='Trạng thái', default='draft', required=True)

    # Một danh sách duy nhất
    line_ids = fields.One2many('dl.wood.pickup.pricelist.line', 'pricelist_id', string='Chi tiết đơn giá')

    _sql_constraints = [
        ('month_unique', 'unique(month)', 'Bảng giá cho tháng này đã tồn tại!')
    ]

    @api.depends('month')
    def _compute_name(self):
        for rec in self:
            if rec.month:
                rec.name = f"Bảng giá Nhặt ván - {rec.month.strftime('%m/%Y')}"
            else:
                rec.name = "Bảng giá mới"

    def action_confirm(self):
        """Xác nhận bảng giá và hủy kích hoạt các bảng cũ"""
        self.ensure_one()
        # Tìm bảng giá đang active khác
        active_pricelists = self.search([('state', '=', 'active'), ('id', '!=', self.id)])
        if active_pricelists:
            active_pricelists.write({'state': 'expired'})
        
        self.write({'state': 'active'})

    def action_calculate_monthly_settlement(self):
        """Tính toán lại lương cả tháng dựa trên điều kiện Bảo hiểm và Số công"""
        self.ensure_one()
        # 1. Tìm khoảng thời gian của tháng này
        start_date = self.month.replace(day=1)
        import calendar
        _, last_day = calendar.monthrange(start_date.year, start_date.month)
        end_date = start_date.replace(day=last_day)
        
        # 2. Lấy tất cả các phiếu sản lượng trong tháng
        productions = self.env['dl.wood.pickup.production'].search([
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('state', 'in', ['confirmed', 'settled'])
        ])
        
        if not productions:
            return
            
        attendances = productions.mapped('attendance_ids')
        employees = attendances.mapped('employee_id')
        
        # 3. Tính toán tổng công tháng cho từng nhân viên
        # Sử dụng dict để tối ưu tốc độ
        emp_total_weight = {}
        for att in attendances:
            emp_id = att.employee_id.id
            emp_total_weight[emp_id] = emp_total_weight.get(emp_id, 0.0) + att.attendance_value
            
        # 4. Cập nhật trạng thái qualify và tính lại lương
        for att in attendances:
            emp = att.employee_id
            total_w = emp_total_weight.get(emp.id, 0.0)
            
            # Điều kiện: Có tích bảo hiểm VÀ đạt đủ số công tối thiểu
            is_qualified = emp.x_has_insurance and total_w >= self.min_workdays
            
            att.write({
                'month_total_weight': total_w,
                'is_qualified': is_qualified
            })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành công'),
                'message': _('Đã quyết toán công và áp đơn giá mới cho nhân viên đủ điều kiện.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_load_products(self):
        """Tự động tải danh sách sản phẩm nhặt ván dựa trên công đoạn"""
        self.ensure_one()
        # Tìm các sản phẩm thuộc công đoạn Nhặt ván
        products = self.env['product.product'].search([
            ('x_production_stage_ids.x_is_nhat_van', '=', True)
        ])
        existing_products = self.line_ids.mapped('product_id')
        
        lines = []
        for product in products:
            if product not in existing_products:
                lines.append((0, 0, {
                    'product_id': product.id,
                }))
        if lines:
            self.write({'line_ids': lines})

class WoodPickupPricelistLine(models.Model):
    _name = 'dl.wood.pickup.pricelist.line'
    _description = 'Chi tiết đơn giá Nhặt ván'

    pricelist_id = fields.Many2one('dl.wood.pickup.pricelist', string='Bảng giá', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Sản phẩm', required=True, 
                                domain=[('dl_is_pickup_process', '=', True)])
    
    # Cấu hình trên cùng 1 dòng
    price_new = fields.Float(string='Giá mới (Đủ ĐK)', digits=(16, 2))
    price_old = fields.Float(string='Giá cũ (Ko ĐK)', digits=(16, 2))
    price_bonus_extra = fields.Float(string='Thưởng vượt 280 bó', digits=(16, 2), 
                                    help="Mỗi bó vượt 280 sẽ được cộng thêm khoản này")

    _sql_constraints = [
        ('prod_unique', 'unique(pricelist_id, product_id)', 'Sản phẩm này đã tồn tại trong bảng giá!')
    ]
