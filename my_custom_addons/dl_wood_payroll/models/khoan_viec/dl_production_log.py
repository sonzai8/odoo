# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductionLog(models.Model):
    _name = 'dl.production.log'
    _description = 'Ghi nhận sản lượng hàng ngày'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    date = fields.Date(string='Ngày', default=fields.Date.today(), required=True, tracking=True)
    production_group_id = fields.Many2one(
        'dl.production.group', 
        string='Tổ sản xuất', 
        required=True, 
        tracking=True
    )
    department_id = fields.Many2one(
        related='production_group_id.department_id', 
        string='Công đoạn sản xuất', 
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
    
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('confirmed', 'Đã xác nhận'),
        ('locked', 'Đã khóa')
    ], string='Trạng thái', default='draft', tracking=True)
    
    # Packaging Materials (KCS only)
    x_plastic_belt_qty = fields.Float(string='Dây đai nhựa (cuộn)', tracking=True)
    x_steel_belt_qty = fields.Float(string='Dây đai sắt (cuộn)', tracking=True)
    x_paper_qty = fields.Float(string='Giấy (kg)', tracking=True)
    x_cardboard_qty = fields.Float(string='Bìa (tấm)', tracking=True)

    # Tạm tính lương (Real-time Estimation)
    x_total_estimated_wage = fields.Monetary(string='Tổng tiền lương tạm tính', compute='_compute_estimated_wages', currency_field='currency_id')
    x_worker_count = fields.Integer(string='Số người tham gia', compute='_compute_estimated_wages')
    x_avg_wage_per_worker = fields.Monetary(string='Lương dự kiến/Người', compute='_compute_estimated_wages', currency_field='currency_id')
    
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    @api.depends('product_line_ids.price', 'product_line_ids.quantity', 'worker_line_ids')
    def _compute_estimated_wages(self):
        for rec in self:
            total_wage = sum(line.price * line.quantity for line in rec.product_line_ids)
            worker_count = len(rec.worker_line_ids)
            rec.x_total_estimated_wage = total_wage
            rec.x_worker_count = worker_count
            rec.x_avg_wage_per_worker = total_wage / worker_count if worker_count > 0 else 0.0

    product_line_ids = fields.One2many(
        'dl.production.log.product.line', 
        'production_log_id', 
        string='Chi tiết sản phẩm'
    )
    
    worker_line_ids = fields.One2many(
        'dl.worker.log.line', 
        'production_log_id', 
        string='Chi tiết nhân viên'
    )

    @api.onchange('production_group_id')
    def _onchange_production_group_id(self):
        if self.production_group_id:
            lines = []
            for employee in self.production_group_id.member_ids:
                lines.append((0, 0, {
                    'employee_id': employee.id,
                    'worked_hours': 1.0,
                }))
            self.worker_line_ids = [(5, 0, 0)] + lines

    def action_confirm(self):
        for rec in self:
            if any(line.price <= 0 for line in rec.product_line_ids):
                raise ValidationError(_("Một số sản phẩm trong phiếu này chưa có đơn giá. Vui lòng kiểm tra Bảng giá công đoạn của tháng."))
        self.write({'state': 'confirmed'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_lock(self):
        self.write({'state': 'locked'})

    def action_unlock(self):
        self.write({'state': 'confirmed'})

    def action_save(self):
        """Dummy action to trigger form save via header button"""
        return True


class ProductionLogProductLine(models.Model):
    _name = 'dl.production.log.product.line'
    _description = 'Chi tiết sản phẩm sản xuất'

    production_log_id = fields.Many2one('dl.production.log', string='Bản ghi sản lượng', ondelete='cascade')
    date = fields.Date(related='production_log_id.date', store=True, index=True)
    production_group_id = fields.Many2one(
        related='production_log_id.production_group_id', 
        string='Tổ sản xuất', 
        store=True, 
        index=True
    )
    workshop_id = fields.Many2one(
        related='production_log_id.production_group_id.x_workshop_id', 
        string='Xưởng', 
        store=True, 
        index=True
    )
    department_id = fields.Many2one(related='production_log_id.department_id', store=True, index=True)
    
    product_id = fields.Many2one('product.product', string='Sản phẩm', required=True)
    x_is_support_product = fields.Boolean(related='product_id.x_is_support_product', string='Sản phẩm hỗ trợ', store=True, readonly=True)
    
    # Thông số từ sản phẩm (Read-only)
    x_thickness = fields.Float(related='product_id.x_thickness', string='Độ dày (mm)', readonly=True)
    x_length = fields.Float(related='product_id.x_length', string='Dài (cm)', readonly=True)
    x_width = fields.Float(related='product_id.x_width', string='Rộng (cm)', readonly=True)
    
    # Các trường mở rộng cho bước Ép Film
    x_film_brand_id = fields.Many2one('dl.film.brand', string='Thương hiệu Film')
    x_surface_type = fields.Selection([
        ('1m', 'Phủ 1 mặt (1M)'),
        ('2m', 'Phủ 2 mặt (2M)'),
    ], string='Số mặt phủ', default='2m')
    
    x_quality = fields.Selection(related='product_id.x_quality', string='Chất lượng', readonly=True)
    layer_info = fields.Char(related='product_id.x_structure_summary', string='Thông số kỹ thuật', readonly=True)
    
    quantity = fields.Float(string='Số lượng', default=1.0, required=True)
    
    x_price_type = fields.Selection([
        ('standard_new', 'Thường - Mới'),
        ('standard_old', 'Thường - Cũ'),
        ('repair_new', 'Sửa - Mới'),
        ('repair_old', 'Sửa - Cũ'),
    ], string='Loại đơn giá', default='standard_new', required=True)
    
    is_re_ep_film = fields.Boolean(string='Ép lại', default=False)
    
    price = fields.Float(string='Đơn giá', compute='_compute_price', store=True)
    extra_price = fields.Float(string='Đơn giá lũy tiến', compute='_compute_price', store=True)

    @api.depends(
        'production_log_id.date', 'production_log_id.department_id', 
        'product_id', 'x_price_type', 'is_re_ep_film',
        'x_film_brand_id', 'x_surface_type'
    )
    def _compute_price(self):
        for rec in self:
            if not rec.production_log_id.date or not rec.production_log_id.department_id or not rec.product_id:
                rec.price = 0.0
                rec.extra_price = 0.0
                continue
            
            # Kiểm tra xem có phải công đoạn Ép Film không
            dept_name = rec.department_id.name.upper() if rec.department_id else ''
            if 'ÉP FILM' in dept_name or 'EP FILM' in dept_name:
                # Dùng ma trận giá Ép Film
                # Ưu tiên lấy alias từ ký hiệu độ dày (x_thickness_alias của sản phẩm)
                res = self.env['dl.film.pricelist']._get_film_active_price(
                    rec.date, 
                    rec.product_id.product_tmpl_id.id, 
                    rec.x_film_brand_id.id, 
                    rec.x_surface_type
                )
                
                # Tự động xác định đơn giá (Ưu tiên lấy giá CAO cho nhật ký hàng ngày)
                if rec.is_re_ep_film:
                    rec.price = res.get('price_re_ep_high', 0.0)
                else:
                    rec.price = res.get('price_high', 0.0)
                
                rec.extra_price = 0.0
            else:
                # Dùng bảng giá công đoạn thông thường
                res = self.env['dl.piece.rate.pricelist']._get_active_price(
                    rec.production_log_id.date, 
                    rec.production_log_id.department_id, 
                    rec.product_id
                )
                rec.price = res.get('price_high', 0.0)
                rec.extra_price = res.get('extra_price', 0.0)


class WorkerLogLine(models.Model):
    _name = 'dl.worker.log.line'
    _description = 'Chi tiết phân bổ công nhân viên'

    production_log_id = fields.Many2one('dl.production.log', string='Bản ghi sản lượng', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True)
    worked_hours = fields.Float(string='Số công (h)', default=1.0, required=True)
    
    source_group_id = fields.Many2one(
        related='employee_id.x_source_group_id', 
        string='Tổ gốc', 
        readonly=True, 
        store=True
    )
    
    native_group_id = fields.Many2one('dl.production.group', string='Tổ biên chế')
    actual_group_id = fields.Many2one('dl.production.group', string='Tổ thực tế làm việc')
    
    transfer_status = fields.Selection([
        ('native', 'Biên chế'),
        ('lent_out', 'Cho mượn'),
        ('borrowed_in', 'Mượn người')
    ], string='Phân loại Mượn')

    handshake_status = fields.Selection([
        ('n/a', '-'),
        ('pending', 'Chờ duyệt'),
        ('confirmed', 'Đã duyệt'),
        ('rejected', 'Từ chối')
    ], string='Duyệt', default='n/a')

    is_attendance_missing = fields.Boolean(
        string='Thiếu chấm công', 
        compute='_compute_is_attendance_missing'
    )

    def _compute_is_attendance_missing(self):
        for line in self:
            if line.employee_id and line.production_log_id.date:
                att_count = self.env['dl.daily.attendance.line'].search_count([
                    ('employee_id', '=', line.employee_id.id),
                    ('date', '=', line.production_log_id.date)
                ])
                line.is_attendance_missing = att_count == 0
            else:
                line.is_attendance_missing = False
