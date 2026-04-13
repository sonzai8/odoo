# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ProductionLog(models.Model):
    _name = 'dl.production.log'
    _description = 'Ghi nhận sản lượng hàng ngày'
    _order = 'date desc, id desc'

    date = fields.Date(string='Ngày', default=fields.Date.today(), required=True)
    work_center_id = fields.Many2one('mrp.workcenter', string='Tổ thực hiện', required=True)
    product_id = fields.Many2one('product.product', string='Sản phẩm', required=True)
    
    # Các thuộc tính tra cứu giá
    thickness_id = fields.Many2one('product.attribute.value', string='Độ dày', domain="[('attribute_id.name', 'ilike', 'Độ dày')]")
    size_id = fields.Many2one('product.attribute.value', string='Kích thước', domain="[('attribute_id.name', 'ilike', 'Kích thước')]")
    film_type_id = fields.Many2one('product.attribute.value', string='Loại Phim', domain="[('attribute_id.name', 'ilike', 'Loại Phim')]")
    surface_id = fields.Many2one('product.attribute.value', string='Bề mặt', domain="[('attribute_id.name', 'ilike', 'Bề mặt')]")
    
    quantity = fields.Float(string='Số lượng', default=1.0, required=True)
    is_re_ep_film = fields.Boolean(string='Ép 1 mặt', help='Nếu True tính đơn giá ép 1 mặt')
    
    price = fields.Float(string='Đơn giá', compute='_compute_price', store=True)
    extra_price = fields.Float(string='Đơn giá lũy tiến', compute='_compute_price', store=True)

    worker_line_ids = fields.One2many(
        'dl.worker.log.line', 
        'production_log_id', 
        string='Chi tiết nhân viên'
    )

    @api.depends('date', 'work_center_id', 'thickness_id', 'size_id', 'film_type_id', 'surface_id', 'is_re_ep_film')
    def _compute_price(self):
        for rec in self:
            price, extra = self.env['dl.piece.rate.pricelist']._get_active_price(
                rec.date, 
                rec.work_center_id, 
                rec.thickness_id, 
                rec.size_id, 
                rec.film_type_id, 
                rec.surface_id
            )
            rec.price = price
            rec.extra_price = extra

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(vals_list)


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

    @api.depends('employee_id', 'production_log_id.work_center_id', 'source_group_id')
    def _compute_is_borrowed(self):
        for line in self:
            if line.employee_id and line.production_log_id.work_center_id and line.source_group_id:
                # Nếu Tổ gốc (Group) thuộc một Công đoạn khác với Công đoạn thực hiện
                line.is_borrowed = line.source_group_id.work_center_id.id != line.production_log_id.work_center_id.id
            else:
                line.is_borrowed = False
