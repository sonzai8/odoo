# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DlMisaExtensionRelease(models.Model):
    _name = 'dl.misa.extension.release'
    _description = 'Lịch sử Phiên bản Odoo Bridge Extension'
    _order = 'date_release desc, id desc'

    name = fields.Char(string='Phiên bản', required=True, help='Ví dụ: 1.1')
    date_release = fields.Datetime(string='Ngày phát hành', default=fields.Datetime.now, required=True)
    zip_file = fields.Binary(string='File ZIP Cài đặt', attachment=True, required=True)
    filename = fields.Char(string='Tên file', default='OdooBridgeUpdate.zip')
    notes = fields.Text(string='Ghi chú phát hành')
    is_active = fields.Boolean(string='Đang phát hành (Kích hoạt)', default=False, 
                               help='Bản đang được đánh dấu sẽ được sử dụng để phân phối cho nhân viên tải về.')

    @api.model_create_multi
    def create(self, vals_list):
        # Nếu có bản ghi nào set is_active = True, thì phải bỏ is_active của các bản cũ
        for vals in vals_list:
            if vals.get('is_active'):
                self.search([('is_active', '=', True)]).write({'is_active': False})
        return super(DlMisaExtensionRelease, self).create(vals_list)

    def write(self, vals):
        if vals.get('is_active'):
            # Bỏ is_active của các bản ghi khác
            self.search([('id', 'not in', self.ids), ('is_active', '=', True)]).write({'is_active': False})
        return super(DlMisaExtensionRelease, self).write(vals)

    def action_activate(self):
        """Action để bấm nút Kích hoạt trên Form hoặc List view"""
        for record in self:
            record.is_active = True
