# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SortingPricelist(models.Model):
    _name = 'dl.sorting.pricelist'
    _description = 'Bảng giá Nhặt Ván'
    _order = 'create_date desc'

    name = fields.Char(string='Tên bảng giá', required=True, default="Bảng giá Nhặt Ván")
    active = fields.Boolean(default=True)

    # Đơn giá 1.7 ly
    price_17_base_new = fields.Float(string='1.7 Ly - Dưới 280 (Mới)', digits=(16, 2))
    price_17_bonus_new = fields.Float(string='1.7 Ly - Trên 280 (Mới)', digits=(16, 2))
    price_17_base_old = fields.Float(string='1.7 Ly - Dưới 280 (Cũ)', digits=(16, 2))
    price_17_bonus_old = fields.Float(string='1.7 Ly - Trên 280 (Cũ)', digits=(16, 2))

    # Đơn giá 2.0 ly
    price_20_base_new = fields.Float(string='2.0 Ly - Dưới 280 (Mới)', digits=(16, 2))
    price_20_bonus_new = fields.Float(string='2.0 Ly - Trên 280 (Mới)', digits=(16, 2))
    price_20_base_old = fields.Float(string='2.0 Ly - Dưới 280 (Cũ)', digits=(16, 2))
    price_20_bonus_old = fields.Float(string='2.0 Ly - Trên 280 (Cũ)', digits=(16, 2))

    @api.model
    def get_latest_price(self):
        return self.search([], limit=1, order='create_date desc')
