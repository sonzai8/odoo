# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    x_wood_prefix = fields.Char(
        related='company_id.x_wood_prefix',
        string='Mã công ty',
        readonly=False
    )
    x_representative = fields.Char(
        related='company_id.x_representative',
        string='Người đại diện công ty',
        readonly=False
    )
    x_representative_position = fields.Char(
        related='company_id.x_representative_position',
        string='Chức vụ đại diện',
        readonly=False
    )
    x_inventory_inspector = fields.Char(
        related='company_id.x_inventory_inspector',
        string='Người kiểm kê',
        readonly=False
    )
    x_inventory_inspector_position = fields.Char(
        related='company_id.x_inventory_inspector_position',
        string='Chức danh người kiểm kê',
        readonly=False
    )
    x_prep_days = fields.Integer(
        related='company_id.x_prep_days',
        string='Thời gian chuẩn bị mặc định (ngày)',
        readonly=False
    )
    x_exploitation_capacity = fields.Integer(
        related='company_id.x_exploitation_capacity',
        string='Năng lực khai thác mặc định (m³/ngày)',
        readonly=False
    )
    x_misa_product_code_regex = fields.Char(
        string='Regex kiểm tra mã Sản phẩm MISA', 
        config_parameter='misa.product_code_regex', 
        default='^sonzai'
    )
    x_misa_product_code_error_msg = fields.Char(
        string='Câu báo lỗi khi sai Mã', 
        config_parameter='misa.product_code_error_msg', 
        default='Mã sản phẩm bắt buộc phải bắt đầu bằng chữ "sonzai".'
    )
