# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    x_wood_prefix = fields.Char(string='Tiền tố mã Gỗ', default='QTP', help='Tiền tố dùng để sinh mã Hồ sơ và Lệnh sản xuất (VD: QTP)')
