# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

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
    work_center_id = fields.Many2one(
        related='production_group_id.work_center_id', 
        string='Tổ thực hiện (Công đoạn)', 
        store=True, 
        readonly=True
    )
    
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('confirmed', 'Đã xác nhận'),
        ('locked', 'Đã khóa')
    ], string='Trạng thái', default='draft', tracking=True)

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
            # Gợi ý toàn bộ nhân viên thuộc tổ vào tab nhân sự
            lines = []
            for employee in self.production_group_id.member_ids:
                lines.append((0, 0, {
                    'employee_id': employee.id,
                    'worked_hours': 1.0,
                }))
            self.worker_line_ids = [(5, 0, 0)] + lines

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_lock(self):
        self.write({'state': 'locked'})

    def action_unlock(self):
        self.write({'state': 'confirmed'})


class ProductionLogProductLine(models.Model):
    _name = 'dl.production.log.product.line'
    _description = 'Chi tiết sản phẩm sản xuất'

    production_log_id = fields.Many2one('dl.production.log', string='Bản ghi sản lượng', ondelete='cascade')
    date = fields.Date(related='production_log_id.date', store=True)
    work_center_id = fields.Many2one(related='production_log_id.work_center_id', store=True)
    
    product_id = fields.Many2one('product.product', string='Sản phẩm', required=True)
    
    # Thông số từ sản phẩm (Read-only)
    x_thickness = fields.Float(related='product_id.x_thickness', string='Độ dày (mm)', readonly=True)
    layer_info = fields.Char(related='product_id.x_structure_summary', string='Cấu trúc', readonly=True)
    film_type_id = fields.Many2one(related='product_id.x_film_id', string='Loại Phim', readonly=True)
    surface_type = fields.Selection(related='product_id.x_surface_type', string='Quy cách phủ', readonly=True)
    
    quantity = fields.Float(string='Số lượng', default=1.0, required=True)
    is_re_ep_film = fields.Boolean(string='Ép lại 1 mặt')
    
    price = fields.Float(string='Đơn giá', compute='_compute_price', store=True)
    extra_price = fields.Float(string='Đơn giá lũy tiến', compute='_compute_price', store=True)

    @api.depends('production_log_id.date', 'production_log_id.work_center_id', 'product_id', 'is_re_ep_film')
    def _compute_price(self):
        for rec in self:
            # Nếu ép lại 1 mặt, thông thường giá sẽ tra cứu theo Sản phẩm hoặc có logic riêng.
            # Với mô hình mới, ta tra cứu theo Product ID.
            price, extra = self.env['dl.piece.rate.pricelist']._get_active_price(
                rec.production_log_id.date, 
                rec.production_log_id.work_center_id, 
                rec.product_id
            )
            rec.price = price
            rec.extra_price = extra


class WorkerLogLine(models.Model):
    _name = 'dl.worker.log.line'
    _description = 'Chi tiết phân bổ công nhân viên'

    production_log_id = fields.Many2one('dl.production.log', string='Bản ghi sản lượng', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True)
    worked_hours = fields.Float(string='Số công (h)', default=1.0, required=True)
    
    # Related fields
    source_group_id = fields.Many2one(
        related='employee_id.x_source_group_id', 
        string='Tổ gốc', 
        readonly=True, 
        store=True
    )
    
    # Logic mượn người
    is_borrowed = fields.Boolean(
        string='Mượn người', 
        compute='_compute_is_borrowed', 
        store=True
    )

    @api.depends('employee_id', 'production_log_id.production_group_id', 'source_group_id')
    def _compute_is_borrowed(self):
        for line in self:
            if line.employee_id and line.production_log_id.production_group_id and line.source_group_id:
                # Nếu Tổ gốc khác với Tổ sản xuất đang thực hiện phiếu
                line.is_borrowed = line.source_group_id.id != line.production_log_id.production_group_id.id
            else:
                line.is_borrowed = False
