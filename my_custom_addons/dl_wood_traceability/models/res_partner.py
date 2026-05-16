# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'dl.wood.log.mixin']

    dl_contract_ids = fields.One2many(
        'dl.wood.contract.template', 
        'partner_id', 
        string='Danh sách hợp đồng mẫu'
    )

    # Sửa nhãn dịch sai từ 'Trạng thái' thành 'Tỉnh / Thành phố'
    state_id = fields.Many2one("res.country.state", string='Tỉnh / Thành phố')
    city = fields.Char(string='Xã / Phường')
    x_customer_code = fields.Char(string='Mã khách hàng', index=True, help='Mã khách hàng phải đồng bộ với phần mềm Misa')
    x_woodpro_id = fields.Char(string='ID WoodPro', index=True)
    x_is_wood_supplier = fields.Selection([
        ('owner', 'Chủ Rừng'),
        ('supplier', 'Nhà Cung Cấp Gỗ')
    ], string='Loại đối tác gỗ')
    x_is_wood_customer = fields.Boolean(string='Khách hàng mua gỗ', default=False,
                                         help='Đánh dấu đây là khách hàng mua gỗ thành phẩm từ công ty.')

    exploitation_location_ids = fields.One2many(
        'dl.wood.exploitation.location', 
        'partner_id', 
        string='Địa điểm khai thác'
    )

    @api.model_create_multi
    def create(self, vals_list):
        partners = super(ResPartner, self).create(vals_list)
        for partner in partners:
            if partner.x_is_wood_supplier == 'owner' and not partner.exploitation_location_ids:
                # Tạo địa điểm khai thác mặc định từ địa chỉ của partner
                self.env['dl.wood.exploitation.location'].create({
                    'partner_id': partner.id,
                    'name': _('Địa điểm chính (Từ địa chỉ chủ rừng)'),
                    'street': partner.street,
                    'city': partner.city,
                    'state_id': partner.state_id.id,
                    'is_main': True
                })
        return partners

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        for partner in self:
            if partner.x_is_wood_supplier == 'owner' and not partner.exploitation_location_ids:
                # Tạo địa điểm khai thác mặc định nếu chưa có
                self.env['dl.wood.exploitation.location'].create({
                    'partner_id': partner.id,
                    'name': _('Địa điểm chính (Từ địa chỉ chủ rừng)'),
                    'street': partner.street,
                    'city': partner.city,
                    'state_id': partner.state_id.id,
                    'is_main': True
                })
        return res
