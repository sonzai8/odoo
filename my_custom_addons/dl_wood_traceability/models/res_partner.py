# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from .address_utils import format_vietnamese_address

class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'dl.wood.log.mixin']

    @api.model
    def default_get(self, fields_list):
        res = super(ResPartner, self).default_get(fields_list)
        if 'lang' in fields_list:
            res['lang'] = 'vi_VN'
        return res

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
            partner.x_full_address = format_vietnamese_address(
                street=partner.street,
                street2=partner.street2,
                city=partner.city,
                state_name=partner.state_id.name
            )

    x_short_name = fields.Char(
        string='Tên rút gọn',
        compute='_compute_x_short_name',
        store=True,
        readonly=False
    )

    @api.depends('name', 'is_company')
    def _compute_x_short_name(self):
        import re
        prefixes = [
            # 1. Các tiền tố siêu dài (dịch vụ, thương mại, đầu tư, xuất nhập khẩu...)
            r'^công ty cổ phần đầu tư xây dựng hạ tầng kinh tế\s+',
            r'^công ty cổ phần sản xuất và xuất nhập khẩu\s+',
            r'^công ty cổ phần xây dựng và dịch vụ thương mại\s+',
            r'^công ty cổ phần sản xuất và thương mại\s+',
            r'^công ty cổ phần thương mại và đầu tư\s+',
            r'^công ty cổ phần xây dựng và thương mại\s+',
            r'^công ty cổ phần xây dựng thương mại\s+',
            r'^công ty cp xây dựng thương mại\s+',
            r'^công ty cổ phần thương mại và xây dựng\s+',
            r'^công ty tnhh xuất nhập khẩu\s+',
            
            # 2. Các tiền tố dài trung bình đã có sẵn
            r'^công ty tnhh mtv\s+',
            r'^công ty tnhh một thành viên\s+',
            r'^công ty tnhh sx & tm\s+',
            r'^công ty tnhh sản xuất & thương mại\s+',
            r'^công ty tnhh tm & sx\s+',
            r'^công ty tnhh thương mại & sản xuất\s+',
            r'^công ty tnhh sx\s+',
            r'^công ty tnhh tm\s+',
            r'^công ty tnhh thương mại\s+',
            r'^công ty tnhh\s+',
            r'^công ty cổ phần\s+',
            r'^công ty cp\s+',
            r'^cty tnhh\s+',
            r'^cty cp\s+',
            r'^dntn\s+',
            r'^doanh nghiệp tư nhân\s+',
        ]
        for partner in self:
            if not partner.is_company:
                partner.x_short_name = False
                continue
            if partner.x_short_name:
                continue
            name = partner.name or ""
            short_name = name
            
            # Quét và xóa các tiền tố công ty (Không phân biệt chữ hoa thường)
            for prefix in prefixes:
                match = re.search(prefix, short_name, re.IGNORECASE)
                if match:
                    short_name = re.sub(prefix, '', short_name, flags=re.IGNORECASE)
                    break
            
            # Xóa các khoảng trắng thừa hoặc ký tự gạch nối
            short_name = short_name.strip(" -_")
            partner.x_short_name = short_name

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
