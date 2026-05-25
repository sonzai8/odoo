# -*- coding: utf-8 -*-
from odoo import models, fields

class ResCountryState(models.Model):
    _inherit = 'res.country.state'
    
    # Trường tùy chỉnh để ưu tiên hiển thị
    x_sequence = fields.Integer(string='Thứ tự hiển thị', default=1000)
    
    # Ghi đè luật sắp xếp mặc định
    _order = 'x_sequence ASC, code ASC, name ASC'
