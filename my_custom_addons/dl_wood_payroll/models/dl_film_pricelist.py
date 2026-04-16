# -*- coding: utf-8 -*-
"""
Bảng giá Ép Film theo từng tháng.
Logic: giá tra cứu theo (Alias độ dày + Thương hiệu Film + Số mặt phủ)
  - Đủ công → price_high
  - Thiếu công → price_low
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class FilmPricelist(models.Model):
    _name = 'dl.film.pricelist'
    _inherit = ['mail.thread']
    _description = 'Bảng giá Ép Film theo tháng'
    _order = 'year desc, month desc'

    name = fields.Char(string='Mã bảng giá', required=False, copy=False, default='/')
    month = fields.Integer(string='Tháng', required=True, default=lambda self: fields.Date.today().month)
    year = fields.Integer(string='Năm', required=True, default=lambda self: fields.Date.today().year)
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('confirmed', 'Xác nhận'),
    ], string='Trạng thái', default='draft', copy=False, tracking=True)

    x_required_days = fields.Float(
        string='Số công tối thiểu',
        default=26.0,
        help='Số công trong tháng để được tính theo Đơn giá Mới (price_high).'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Tiền tệ',
        default=lambda self: self.env.company.currency_id
    )
    line_ids = fields.One2many('dl.film.pricelist.line', 'pricelist_id', string='Chi tiết đơn giá')

    _sql_constraints = [
        ('month_year_unique', 'unique(month, year)', 'Bảng giá Ép Film cho tháng/năm này đã tồn tại!'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        """Tự động đặt tên bảng giá theo tháng/năm"""
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == '/':
                month = vals.get('month', fields.Date.today().month)
                year = vals.get('year', fields.Date.today().year)
                vals['name'] = "EP-FILM-%02d-%d" % (int(month), int(year))
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if 'month' in vals or 'year' in vals:
            for rec in self:
                if rec.state == 'draft':
                    rec.name = "EP-FILM-%02d-%d" % (int(rec.month), int(rec.year))
        return res

    def action_confirm(self):
        """Xác nhận và khóa bảng giá"""
        if not self.env.user.has_group('dl_wood_payroll.group_dl_payroll_manager'):
            raise UserError(_("Chỉ cấp quản lý mới được phép xác nhận bảng giá."))
        self.write({'state': 'confirmed'})

    def action_draft(self):
        """Chuyển về dự thảo"""
        if not self.env.user.has_group('dl_wood_payroll.group_dl_payroll_manager'):
            raise UserError(_("Chỉ cấp quản lý mới được phép mở lại bảng giá."))
        self.write({'state': 'draft'})

    def action_save(self):
        """Trigger lưu form"""
        return True

    def action_open_clone_wizard(self):
        """Mở wizard để chọn tháng nguồn cần clone"""
        self.ensure_one()
        return {
            'name': _('Sao chép từ tháng khác'),
            'type': 'ir.actions.act_window',
            'res_model': 'dl.film.clone.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_target_pricelist_id': self.id},
        }

    def action_open_excel_wizard(self):
        """Mở wizard Import/Export Excel"""
        self.ensure_one()
        return {
            'name': _('Nhập/Xuất Excel Đơn giá Ép Film'),
            'type': 'ir.actions.act_window',
            'res_model': 'dl.film.pricelist.excel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_pricelist_id': self.id},
        }

    @api.model
    def _get_film_active_price(self, date, thickness_alias, film_brand_id, surface_type):
        """
        Tra cứu đơn giá Ép Film dựa trên:
          - date: ngày sản xuất
          - thickness_alias (str): ký hiệu độ dày
          - film_brand_id (int): ID thương hiệu Film
          - surface_type (str): '1m' hoặc '2m'
        Trả về dict {price_low, price_high, required_days}
        """
        empty = {'price_low': 0.0, 'price_high': 0.0, 'required_days': 0.0}
        if not date or not thickness_alias or not film_brand_id or not surface_type:
            return empty

        pricelist = self.search([
            ('month', '=', date.month),
            ('year', '=', date.year),
            ('state', '=', 'confirmed'),
        ], limit=1)

        if not pricelist:
            return empty

        line = self.env['dl.film.pricelist.line'].search([
            ('pricelist_id', '=', pricelist.id),
            ('x_thickness_alias', '=', thickness_alias),
            ('x_film_brand_id', '=', film_brand_id),
            ('x_surface_type', '=', surface_type),
        ], limit=1)

        if line:
            return {
                'price_low': line.price_low,
                'price_high': line.price_high,
                'price_re_ep': line.price_re_ep,
                'required_days': pricelist.x_required_days,
            }
        return empty


class FilmPricelistLine(models.Model):
    _name = 'dl.film.pricelist.line'
    _description = 'Chi tiết đơn giá Ép Film'
    _order = 'x_thickness_alias, x_film_brand_id'

    pricelist_id = fields.Many2one('dl.film.pricelist', string='Bảng giá', ondelete='cascade', required=True)

    x_thickness_alias = fields.Char(string='Ký hiệu độ dày', required=True,
                                    help='Ví dụ: 11M, 14D, 17M, 19D...')
    x_film_brand_id = fields.Many2one('dl.film.brand', string='Thương hiệu Film', required=True)
    x_surface_type = fields.Selection([
        ('1m', '1M'),
        ('2m', '2M'),
    ], string='Số mặt phủ', required=True)

    currency_id = fields.Many2one(related='pricelist_id.currency_id', string='Tiền tệ', store=True)
    price_low = fields.Monetary(
        string='DG Cũ',
        currency_field='currency_id',
        default=0.0,
        help='Áp dụng khi nhân viên không đủ số công yêu cầu trong tháng.'
    )
    price_high = fields.Monetary(
        string='DG Mới',
        currency_field='currency_id',
        default=0.0,
        help='Áp dụng khi nhân viên đủ hoặc vượt số công yêu cầu trong tháng.'
    )
    price_re_ep = fields.Monetary(
        string='Lại',
        currency_field='currency_id',
        default=0.0,
        help='Áp dụng khi sản phẩm được tích là Ép lại 1 mặt.'
    )

    # Related để lọc/báo cáo
    month = fields.Integer(related='pricelist_id.month', store=True, index=True, readonly=True)
    year = fields.Integer(related='pricelist_id.year', store=True, index=True, readonly=True)

    _sql_constraints = [
        ('line_unique', 'unique(pricelist_id, x_thickness_alias, x_film_brand_id, x_surface_type)',
         'Tổ hợp (Alias + Thương hiệu + Số mặt) này đã tồn tại trong bảng giá!'),
    ]

    @api.constrains('x_thickness_alias', 'x_film_brand_id', 'x_surface_type')
    def _check_unique_combination(self):
        """Kiểm tra trùng lặp tổ hợp để báo lỗi chi tiết hơn SQL constraint"""
        for rec in self:
            domain = [
                ('id', '!=', rec.id),
                ('pricelist_id', '=', rec.pricelist_id.id),
                ('x_thickness_alias', '=', rec.x_thickness_alias),
                ('x_film_brand_id', '=', rec.x_film_brand_id.id),
                ('x_surface_type', '=', rec.x_surface_type),
            ]
            if self.search_count(domain) > 0:
                raise UserError(_(
                    "Lỗi: Tổ hợp này đã tồn tại trong bảng giá!\n"
                    "- Độ dày: %s\n"
                    "- Thương hiệu: %s\n"
                    "- Số mặt: %s"
                ) % (rec.x_thickness_alias, rec.x_film_brand_id.name, rec.x_surface_type))

    @api.constrains('price_low', 'price_high', 'price_re_ep')
    def _check_prices(self):
        """Kiểm tra đơn giá không âm"""
        for rec in self:
            if rec.price_low < 0 or rec.price_high < 0 or rec.price_re_ep < 0:
                raise UserError(_("Đơn giá không được phép là số âm (Dòng: %s - %s)") % 
                                (rec.x_thickness_alias, rec.x_film_brand_id.name))
