# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    x_wood_prefix = fields.Char(string='Mã công ty', default='QTP', help='Tiền tố dùng để sinh mã Hồ sơ và Lệnh sản xuất (VD: QTP)')
    x_representative = fields.Char(string='Người đại diện công ty')
    x_representative_position = fields.Char(string='Chức vụ đại diện')
    x_inventory_inspector = fields.Char(string='Người kiểm kê')
    x_inventory_inspector_position = fields.Char(string='Chức danh người kiểm kê')
    x_prep_days = fields.Integer(string='Thời gian chuẩn bị mặc định (ngày)', default=6)
    x_exploitation_capacity = fields.Integer(string='Năng lực khai thác mặc định (m³/ngày)', default=40)
    
    # Extension MISA config
    x_misa_ext_token = fields.Char(string='Token bảo mật tải Extension', copy=False)
