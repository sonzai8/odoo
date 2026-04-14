# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    x_length = fields.Float(string='Chiều dài (m)', digits=(16, 2))
    x_width = fields.Float(string='Chiều rộng (m)', digits=(16, 2))
