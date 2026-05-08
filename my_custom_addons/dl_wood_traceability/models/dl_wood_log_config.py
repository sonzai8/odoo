# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DLWoodLogConfig(models.Model):
    _name = 'dl.wood.log.config'
    _description = 'Cấu hình Nhật ký Log'

    name = fields.Char(string='Tên cấu hình', compute='_compute_name', store=True)
    model_id = fields.Many2one('ir.model', string='Model cần theo dõi', required=True, index=True, ondelete='cascade',
                              domain=[('model', 'ilike', 'dl.')]) # Ưu tiên các model dl_
    field_ids = fields.Many2many('ir.model.fields', string='Các trường theo dõi',
                                domain="[('model_id', '=', model_id), ('ttype', 'not in', ['one2many', 'many2many', 'binary'])]")
    
    log_create = fields.Boolean(string='Theo dõi Tạo mới', default=True)
    log_write = fields.Boolean(string='Theo dõi Cập nhật', default=True)
    log_unlink = fields.Boolean(string='Theo dõi Xóa', default=True)
    
    active = fields.Boolean(string='Đang hoạt động', default=True)

    _model_unique = models.Constraint(
        'unique(model_id)', 'Mỗi model chỉ được cấu hình một lần!'
    )

    @api.depends('model_id')
    def _compute_name(self):
        for rec in self:
            rec.name = f"Log Config: {rec.model_id.name}" if rec.model_id else "New Config"
