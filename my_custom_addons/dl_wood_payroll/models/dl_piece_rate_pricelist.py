# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PieceRatePricelist(models.Model):
    _name = 'dl.piece.rate.pricelist'
    _inherit = ['mail.thread'] # Cần mail module để sử dụng tracking
    _description = 'Bảng giá đơn giá công đoạn'
    _order = 'year desc, month desc'

    name = fields.Char(string='Tên bảng giá', required=True, copy=False)
    month = fields.Integer(string='Tháng', default=lambda self: fields.Date.today().month, required=True)
    year = fields.Integer(string='Năm', default=lambda self: fields.Date.today().year, required=True)
    state = fields.Selection([
        ('draft', 'Mới'),
        ('confirmed', 'Xác nhận')
    ], string='Trạng thái', default='draft', copy=False, tracking=True)
    
    line_ids = fields.One2many(
        'dl.piece.rate.pricelist.line', 
        'pricelist_id', 
        string='Chi tiết đơn giá'
    )

    # Odoo 19 Constraint Syntax
    _month_year_unique = models.Constraint(
        "UNIQUE(month, year)",
        "Bảng giá cho tháng/năm này đã tồn tại!"
    )

    def action_confirm(self):
        if not self.env.user.has_group('dl_wood_payroll.group_dl_payroll_manager'):
            raise UserError(_("Chỉ cấp quản lý mới được phép xác nhận bảng giá."))
        self.write({'state': 'confirmed'})

    def action_draft(self):
        if not self.env.user.has_group('dl_wood_payroll.group_dl_payroll_manager'):
            raise UserError(_("Chỉ cấp quản lý mới được phép chuyển về bản nháp."))
        self.write({'state': 'draft'})

    def action_clone_pricelist(self):
        self.ensure_one()
        if self.state == 'confirmed':
            raise UserError(_("Không thể clone vào bảng giá đã xác nhận."))
        
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
            raise UserError(_("Không tìm thấy bảng giá đã xác nhận của tháng %s/%s để sao chép.") % (prev_month, prev_year))
        
        self.line_ids.unlink()
        
        vals_list = []
        for line in last_pricelist.line_ids:
            vals_list.append({
                'pricelist_id': self.id,
                'work_center_id': line.work_center_id.id,
                'thickness_id': line.thickness_id.id,
                'size_id': line.size_id.id,
                'film_type_id': line.film_type_id.id,
                'surface_id': line.surface_id.id,
                'price': line.price,
                'extra_price': line.extra_price,
            })
        
        if vals_list:
            self.env['dl.piece.rate.pricelist.line'].create(vals_list)
            
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
    def _get_active_price(self, date, work_center, thickness_id=None, size_id=None, film_type_id=None, surface_id=None):
        """
        Tra cứu đơn giá chính xác tại một thời điểm.
        """
        if not date or not work_center:
            return 0.0, 0.0

        pricelist = self.search([
            ('month', '=', date.month),
            ('year', '=', date.year),
            ('state', '=', 'confirmed')
        ], limit=1)

        if not pricelist:
            return 0.0, 0.0

        domain = [
            ('pricelist_id', '=', pricelist.id),
            ('work_center_id', '=', work_center.id),
        ]
        if thickness_id:
            domain.append(('thickness_id', '=', thickness_id.id))
        if size_id:
            domain.append(('size_id', '=', size_id.id))
        if film_type_id:
            domain.append(('film_type_id', '=', film_type_id.id))
        if wood_grade_id:
            domain.append(('wood_grade_id', '=', wood_grade_id.id))
        if surface_id:
            domain.append(('surface_id', '=', surface_id.id))

        line = self.env['dl.piece.rate.pricelist.line'].search(domain, limit=1)
        if line:
            return line.price, line.extra_price
        return 0.0, 0.0

    @api.model
    def _get_active_price(self, date, work_center, product_id):
        """
        Tra cứu đơn giá chính xác dựa trên sản phẩm cố định.
        """
        if not date or not work_center or not product_id:
            return 0.0, 0.0

        pricelist = self.search([
            ('month', '=', date.month),
            ('year', '=', date.year),
            ('state', '=', 'confirmed')
        ], limit=1)

        if not pricelist:
            return 0.0, 0.0

        line = self.env['dl.piece.rate.pricelist.line'].search([
            ('pricelist_id', '=', pricelist.id),
            ('work_center_id', '=', work_center.id),
            ('product_id', '=', product_id.id)
        ], limit=1)
        
        if line:
            return line.price, line.extra_price
        return 0.0, 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                month = vals.get('month', fields.Date.today().month)
                year = vals.get('year', fields.Date.today().year)
                vals['name'] = f"Bảng giá tháng {month}/{year}"
        return super().create(vals_list)

    def write(self, vals):
        if any(rec.state == 'confirmed' for rec in self):
            if not self.env.user.has_group('dl_wood_payroll.group_dl_payroll_manager'):
                raise UserError(_("Bảng giá đã xác nhận, bạn không có quyền chỉnh sửa."))
        return super().write(vals)


class PieceRatePricelistLine(models.Model):
    _name = 'dl.piece.rate.pricelist.line'
    _description = 'Chi tiết đơn giá công đoạn'

    pricelist_id = fields.Many2one('dl.piece.rate.pricelist', string='Bảng giá', ondelete='cascade')
    work_center_id = fields.Many2one('mrp.workcenter', string='Công đoạn', required=True)
    
    product_id = fields.Many2one('product.product', string='Sản phẩm', required=True)
    
    # Related fields từ sản phẩm (Read-only)
    x_thickness = fields.Float(related='product_id.x_thickness', string='Độ dày (mm)', readonly=True)
    size_id = fields.Many2one(related='product_id.x_dimension_id', string='Kích thước', readonly=True)
    layer_info = fields.Char(related='product_id.x_structure_summary', string='Cấu trúc thực tế', readonly=True)
    film_type_id = fields.Many2one(related='product_id.x_film_id', string='Loại Phim', readonly=True)
    surface_type = fields.Selection(related='product_id.x_surface_type', string='Quy cách phủ', readonly=True)
    
    price = fields.Float(string='Đơn giá', required=True)
    extra_price = fields.Float(string='Đơn giá lũy tiến', help='Dùng cho Nhặt ván khi vượt 280 tấm')
