# -*- coding: utf-8 -*-
"""
Thương hiệu Film dùng cho công đoạn Ép Film.
Mỗi Brand kết hợp với Alias độ dày + Số mặt sẽ cho ra đơn giá cụ thể.
"""
from odoo import models, fields


class FilmBrand(models.Model):
    _name = 'dl.film.brand'
    _description = 'Thương hiệu Film Ép'
    _order = 'name'

    name = fields.Char(string='Tên thương hiệu', required=True)
    code = fields.Char(string='Mã hiệu')
    active = fields.Boolean(string='Đang dùng', default=True)
    note = fields.Text(string='Ghi chú')

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Thương hiệu Film này đã tồn tại!'),
    ]
