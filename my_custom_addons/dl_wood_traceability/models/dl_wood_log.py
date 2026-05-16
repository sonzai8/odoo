# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DLWoodLog(models.Model):
    _name = 'dl.wood.log'
    _description = 'Nhật ký hoạt động Truy xuất gỗ'
    _order = 'datetime desc'

    user_id = fields.Many2one('res.users', string='Người thực hiện', index=True, readonly=True)
    company_id = fields.Many2one(
        'res.company',
        string='Công ty',
        required=True,
        default=lambda self: self.env.company
    )
    datetime = fields.Datetime(string='Thời gian', default=fields.Datetime.now, index=True, readonly=True)
    model_id = fields.Many2one('ir.model', string='Model', index=True, readonly=True, ondelete='cascade')
    model_name = fields.Char(related='model_id.name', string='Tên Model', readonly=True)
    res_id = fields.Integer(string='ID Bản ghi', index=True, readonly=True)
    res_name = fields.Char(string='Bản ghi', readonly=True)
    action = fields.Selection([
        ('create', 'Tạo mới'),
        ('write', 'Cập nhật'),
        ('unlink', 'Xóa')
    ], string='Hành động', index=True, readonly=True)
    
    line_ids = fields.One2many('dl.wood.log.line', 'log_id', string='Chi tiết thay đổi', readonly=True)

class DLWoodLogLine(models.Model):
    _name = 'dl.wood.log.line'
    _description = 'Chi tiết Nhật ký thay đổi'
    _readonly = True

    log_id = fields.Many2one('dl.wood.log', string='Log', ondelete='cascade', index=True)
    field_id = fields.Many2one('ir.model.fields', string='Trường thay đổi', index=True, ondelete='cascade')
    field_desc = fields.Char(related='field_id.field_description', string='Tên trường')
    old_value = fields.Text(string='Giá trị cũ')
    new_value = fields.Text(string='Giá trị mới')
