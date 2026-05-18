# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    x_wood_prefix = fields.Char(string='Tiền tố mã Gỗ', default='QTP', help='Tiền tố dùng để sinh mã Hồ sơ và Lệnh sản xuất (VD: QTP)')
    x_representative = fields.Char(string='Người đại diện công ty')
    x_representative_position = fields.Char(string='Chức vụ đại diện')
