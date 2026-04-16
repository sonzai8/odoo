# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PieceRatePricelist(models.Model):
    _name = 'dl.piece.rate.pricelist'
    _inherit = ['mail.thread']
    _description = 'Bảng giá đơn giá công đoạn'
    _order = 'year desc, month desc'

    name = fields.Char(string='Tên bảng giá', required=False, copy=False, default='/')
    month = fields.Integer(string='Tháng', default=lambda self: fields.Date.today().month, required=True)
    year = fields.Integer(string='Năm', default=lambda self: fields.Date.today().year, required=True)
    state = fields.Selection([
        ('draft', 'Mới'),
        ('confirmed', 'Xác nhận')
    ], string='Trạng thái', default='draft', copy=False, tracking=True)
    
    x_required_days = fields.Float(string='Số công tối thiểu', default=26.0, help='Số công tối thiểu trong tháng để được tính đơn giá cao.')
    
    currency_id = fields.Many2one(
        'res.currency', 
        string='Tiền tệ', 
        default=lambda self: self.env.company.currency_id
    )

    line_ids = fields.One2many(
        'dl.piece.rate.pricelist.line', 
        'pricelist_id', 
        string='Chi tiết đơn giá'
    )

    _sql_constraints = [
        ('month_year_unique', 'unique(month, year)', 'Bảng giá cho tháng/năm này đã tồn tại!')
    ]

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
                'department_id': line.department_id.id,
                'product_id': line.product_id.id,
                'price_low': line.price_low,
                'price_high': line.price_high,
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
    def _get_active_price(self, date, department, product_id):
        """
        Tra cứu đơn giá chính xác dựa trên sản phẩm và công đoạn (Bộ phận).
        """
        if not date or not department or not product_id:
            return {'price_low': 0.0, 'price_high': 0.0, 'extra_price': 0.0, 'required_days': 0.0}

        pricelist = self.search([
            ('month', '=', date.month),
            ('year', '=', date.year),
            ('state', '=', 'confirmed')
        ], limit=1)

        if not pricelist:
            return {'price_low': 0.0, 'price_high': 0.0, 'extra_price': 0.0, 'required_days': 0.0}

        line = self.env['dl.piece.rate.pricelist.line'].search([
            ('pricelist_id', '=', pricelist.id),
            ('department_id', '=', department.id),
            ('product_id', '=', product_id.id)
        ], limit=1)
        
        if line:
            return {
                'price_low': line.price_low,
                'price_high': line.price_high,
                'extra_price': line.extra_price,
                'required_days': pricelist.x_required_days
            }
        return {'price_low': 0.0, 'price_high': 0.0, 'extra_price': 0.0, 'required_days': 0.0}

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == '/':
                month = vals.get('month', fields.Date.today().month)
                year = vals.get('year', fields.Date.today().year)
                vals['name'] = "DON-GIA-%02d-%d" % (int(month), int(year))
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if 'month' in vals or 'year' in vals:
            for rec in self:
                if rec.state == 'draft':
                    rec.name = "DON-GIA-%02d-%d" % (int(rec.month), int(rec.year))
        
        if any(rec.state == 'confirmed' for rec in self):
            if not self.env.user.has_group('dl_wood_payroll.group_dl_payroll_manager'):
                if not (len(vals) == 1 and 'state' in vals):
                    raise UserError(_("Bảng giá đã xác nhận, bạn không có quyền chỉnh sửa."))
        return super().write(vals)

    def action_save(self):
        """Dummy action to trigger form save via header button"""
        return True

    def action_open_excel_wizard(self):
        self.ensure_one()
        return {
            'name': _('Nhập/Xuất Excel Bảng giá'),
            'type': 'ir.actions.act_window',
            'res_model': 'dl.pricelist.excel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_pricelist_id': self.id,
            }
        }


class PieceRatePricelistLine(models.Model):
    _name = 'dl.piece.rate.pricelist.line'
    _description = 'Chi tiết đơn giá công đoạn'

    pricelist_id = fields.Many2one('dl.piece.rate.pricelist', string='Bảng giá', ondelete='cascade')
    department_id = fields.Many2one(
        'hr.department', 
        string='Công đoạn', 
        required=True,
        domain=[('x_is_production_stage', '=', True)]
    )
    
    product_id = fields.Many2one('product.product', string='Sản phẩm', required=True)
    
    # Related fields từ sản phẩm (Read-only)
    x_thickness = fields.Float(related='product_id.x_thickness', string='Độ dày (mm)', readonly=True)
    x_length = fields.Float(related='product_id.x_length', string='Dài (cm)', readonly=True)
    x_width = fields.Float(related='product_id.x_width', string='Rộng (cm)', readonly=True)
    layer_info = fields.Char(related='product_id.x_structure_summary', string='Thông số kỹ thuật', readonly=True)
    film_type_id = fields.Many2one(related='product_id.x_film_id', string='Loại Phim', readonly=True)
    coating_type = fields.Selection(related='product_id.x_coating_type', string='Hình thức phủ', readonly=True)
    
    currency_id = fields.Many2one(related='pricelist_id.currency_id', string='Tiền tệ', store=True)

    price_low = fields.Monetary(string='ĐG cũ', required=True, currency_field='currency_id', default=0.0)
    price_high = fields.Monetary(string='ĐG mới', required=True, currency_field='currency_id', default=0.0)
    
    # Backward compatibility / Display only
    price = fields.Monetary(string='Đơn giá (High)', compute='_compute_legacy_price', currency_field='currency_id', store=True)

    @api.depends('price_high')
    def _compute_legacy_price(self):
        for rec in self:
            rec.price = rec.price_high

    extra_price = fields.Monetary(string='Đơn giá lũy tiến', currency_field='currency_id', help='Dùng cho Nhặt ván khi vượt 280 tấm')

    # Fields for Matrix/Report Filtering (Store=True for Pivot performance)
    month = fields.Integer(related='pricelist_id.month', store=True, index=True, readonly=True)
    year = fields.Integer(related='pricelist_id.year', store=True, index=True, readonly=True)
    workshop_id = fields.Many2one(related='department_id.x_workshop_id', store=True, index=True, readonly=True, string='Xưởng')
    state = fields.Selection(related='pricelist_id.state', store=True, readonly=True, string='Trạng thái bảng giá')
