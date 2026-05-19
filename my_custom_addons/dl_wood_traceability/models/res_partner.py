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

    # CCCD Info
    x_cccd = fields.Char(string='Số CCCD')
    x_cccd_date = fields.Date(string='Ngày cấp CCCD')
    x_cccd_place = fields.Char(string='Nơi cấp CCCD')

    # Thông tin thanh toán (Ngân hàng)
    x_bank_name_id = fields.Many2one('dl.vietnam.bank', string='Ngân hàng')
    x_bank_name = fields.Char(
        string='Ngân hàng (Tên viết tắt)',
        compute='_compute_x_bank_name',
        store=True,
        readonly=False
    )
    x_bank_account_number = fields.Char(string='Số tài khoản')
    x_bank_account_holder = fields.Char(
        string='Chủ tài khoản',
        compute='_compute_x_bank_account_holder',
        store=True,
        readonly=False
    )
    x_full_address = fields.Char(
        string='Địa chỉ đầy đủ',
        compute='_compute_x_full_address',
        store=True
    )

    @api.depends('x_bank_name_id.short_name')
    def _compute_x_bank_name(self):
        for partner in self:
            if partner.x_bank_name_id:
                partner.x_bank_name = partner.x_bank_name_id.short_name
            elif not partner.x_bank_name:
                partner.x_bank_name = ""

    @api.depends('name', 'x_bank_account_number')
    def _compute_x_bank_account_holder(self):
        for partner in self:
            if not partner.x_bank_account_number:
                partner.x_bank_account_holder = partner.name or ""
            else:
                partner.x_bank_account_holder = partner.x_bank_account_holder or ""

    @api.depends('street', 'street2', 'city', 'state_id')
    def _compute_x_full_address(self):
        for partner in self:
            parts = []
            if partner.street:
                parts.append(partner.street)
            if partner.street2:
                parts.append(partner.street2)
                
            city_str = partner.city or ""
            if city_str:
                city_str_cleaned = city_str.strip()
                if not any(city_str_cleaned.startswith(prefix) for prefix in ['Xã', 'Phường', 'Thị trấn', 'xã', 'phường', 'thị trấn', 'Quận', 'Huyện', 'quận', 'huyện']):
                    city_str_cleaned = f"Xã {city_str_cleaned}"
                parts.append(city_str_cleaned)
                
            state_str = partner.state_id.name or ""
            if state_str:
                state_str_cleaned = state_str.strip()
                if not any(state_str_cleaned.startswith(prefix) for prefix in ['Tỉnh', 'Thành phố', 'Tp', 'tỉnh', 'thành phố', 'tp', 'TP']):
                    state_str_cleaned = f"Tỉnh {state_str_cleaned}"
                parts.append(state_str_cleaned)
                
            partner.x_full_address = ", ".join(parts) if parts else ""

    exploitation_location_ids = fields.One2many(
        'dl.wood.exploitation.location', 
        'partner_id', 
        string='Địa điểm khai thác'
    )

    @api.depends('name', 'x_cccd', 'state_id', 'x_is_wood_supplier')
    def _compute_display_name(self):
        super()._compute_display_name()
        for partner in self:
            if partner.x_is_wood_supplier:
                name = partner.name or ""
                cccd = partner.x_cccd or ""
                state = partner.state_id.name or ""
                
                parts = []
                if name:
                    parts.append(name)
                if cccd:
                    parts.append(cccd)
                if state:
                    parts.append(state)
                
                if parts:
                    partner.display_name = " - ".join(parts)
                else:
                    partner.display_name = ""

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
