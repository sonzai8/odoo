# -*- coding: utf-8 -*-
from odoo import models, api, fields
import json

class DLWoodLogMixin(models.AbstractModel):
    _name = 'dl.wood.log.mixin'
    _description = 'Mixin hỗ trợ ghi nhật ký hoạt động'

    def _get_log_config(self):
        return self.env['dl.wood.log.config'].sudo().search([
            ('model_id.model', '=', self._name),
            ('active', '=', True)
        ], limit=1)

    def _format_value(self, field, value):
        if not value:
            return ''
        if field.ttype == 'many2one':
            return value.display_name if hasattr(value, 'display_name') else str(value)
        return str(value)

    @api.model_create_multi
    def create(self, vals_list):
        records = super(DLWoodLogMixin, self).create(vals_list)
        config = self._get_log_config()
        if config and config.log_create:
            for record in records:
                log = self.env['dl.wood.log'].sudo().create({
                    'user_id': self.env.user.id,
                    'model_id': config.model_id.id,
                    'res_id': record.id,
                    'res_name': record.display_name,
                    'action': 'create'
                })
                # Nếu muốn log cả các giá trị ban đầu
                if config.field_ids:
                    for field in config.field_ids:
                        val = record[field.name]
                        if val:
                            self.env['dl.wood.log.line'].sudo().create({
                                'log_id': log.id,
                                'field_id': field.id,
                                'old_value': '',
                                'new_value': self._format_value(field, val)
                            })
        return records

    def write(self, vals):
        config = self._get_log_config()
        if not config or not config.log_write:
            return super(DLWoodLogMixin, self).write(vals)

        # Lưu giá trị cũ trước khi update
        tracked_fields = config.field_ids.mapped('name')
        old_values = {}
        for record in self:
            old_values[record.id] = {f: record[f] for f in vals if f in tracked_fields}

        result = super(DLWoodLogMixin, self).write(vals)

        for record in self:
            log_lines = []
            for field_name, new_val in vals.items():
                if field_name in tracked_fields:
                    field_obj = config.field_ids.filtered(lambda f: f.name == field_name)
                    old_val = old_values[record.id].get(field_name)
                    
                    # So sánh (đơn giản hóa cho chuỗi)
                    if str(old_val) != str(record[field_name]):
                        log_lines.append((0, 0, {
                            'field_id': field_obj.id,
                            'old_value': self._format_value(field_obj, old_val),
                            'new_value': self._format_value(field_obj, record[field_name])
                        }))
            
            if log_lines:
                self.env['dl.wood.log'].sudo().create({
                    'user_id': self.env.user.id,
                    'model_id': config.model_id.id,
                    'res_id': record.id,
                    'res_name': record.display_name,
                    'action': 'write',
                    'line_ids': log_lines
                })
        return result

    def unlink(self):
        config = self._get_log_config()
        if config and config.log_unlink:
            for record in self:
                self.env['dl.wood.log'].sudo().create({
                    'user_id': self.env.user.id,
                    'model_id': config.model_id.id,
                    'res_id': record.id,
                    'res_name': record.display_name,
                    'action': 'unlink'
                })
        return super(DLWoodLogMixin, self).unlink()
