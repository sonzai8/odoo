# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from .address_utils import format_vietnamese_address
import logging
from vietnamadminunits import convert_address
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'dl.wood.log.mixin']

    @api.model
    def default_get(self, fields_list):
        res = super(ResPartner, self).default_get(fields_list)
        if 'lang' in fields_list:
            res['lang'] = 'vi_VN'
            
        is_wood = (
            res.get('x_is_wood_supplier') or 
            res.get('x_is_wood_customer') or 
            self.env.context.get('default_x_is_wood_supplier') or 
            self.env.context.get('default_x_is_wood_customer') or
            self.env.context.get('x_is_wood_supplier') or 
            self.env.context.get('x_is_wood_customer')
        )
        
        is_owner = (
            res.get('x_is_wood_supplier') == 'owner' or 
            self.env.context.get('default_x_is_wood_supplier') == 'owner'
        )

        if 'company_id' in fields_list and is_wood:
            res['company_id'] = self.env.company.id
            
        if is_owner:
            if 'country_id' in fields_list:
                vn_country = self.env['res.country'].search([('code', '=', 'VN')], limit=1)
                if vn_country:
                    res['country_id'] = vn_country.id
            if 'company_type' in fields_list:
                res['company_type'] = 'person'
            if 'is_company' in fields_list:
                res['is_company'] = False
                
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
    def _get_default_prep_days(self):
        try:
            self.env.cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name='res_company' AND column_name='x_prep_days'")
            if self.env.cr.fetchone():
                return self.env.company.x_prep_days or 6
        except Exception:
            pass
        return 6

    def _get_default_exploitation_capacity(self):
        try:
            self.env.cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name='res_company' AND column_name='x_exploitation_capacity'")
            if self.env.cr.fetchone():
                return self.env.company.x_exploitation_capacity or 40
        except Exception:
            pass
        return 40

    x_prep_days = fields.Integer(
        string='Thời gian chuẩn bị (ngày)',
        default=lambda self: self._get_default_prep_days(),
        help='Thời gian chuẩn bị riêng của chủ rừng này. Nếu để 0 sẽ tự động lấy từ cấu hình công ty.'
    )
    x_exploitation_capacity = fields.Integer(
        string='Năng lực khai thác (m³/ngày)',
        default=lambda self: self._get_default_exploitation_capacity(),
        help='Năng lực khai thác riêng của chủ rừng này. Nếu để 0 sẽ tự động lấy từ cấu hình công ty.'
    )

    # CCCD Info
    x_cccd = fields.Char(string='Số CCCD')
    x_cccd_date = fields.Date(string='Ngày cấp CCCD')
    x_cccd_place = fields.Char(string='Nơi cấp CCCD')

    # CCCD QR and Info
    x_qr_cccd_image = fields.Binary("Ảnh QR CCCD")
    x_identity_code = fields.Char("Số CCCD")
    x_birth_date = fields.Date("Ngày sinh")
    x_gender = fields.Selection([('Nam', 'Nam'), ('Nữ', 'Nữ')], string="Giới tính")
    x_issue_date = fields.Date("Ngày cấp")

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

    ward_id = fields.Many2one('res.country.ward', string='Xã/Phường', domain="[('state_id', '=', state_id)]")
    
    @api.depends('street', 'street2', 'city', 'state_id', 'ward_id')
    def _compute_x_full_address(self):
        for partner in self:
            partner.x_full_address = format_vietnamese_address(
                street=partner.street,
                street2=partner.street2,
                ward=partner.ward_id.name if partner.ward_id else None,
                district=partner.city,
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
        for vals in vals_list:
            if vals.get('x_is_wood_supplier') or vals.get('x_is_wood_customer'):
                if 'company_id' not in vals or not vals['company_id'] or vals['company_id'] not in self.env.companies.ids:
                    vals['company_id'] = self.env.company.id
        partners = super(ResPartner, self).create(vals_list)
        for partner in partners:
            if partner.x_is_wood_supplier == 'owner' and not partner.exploitation_location_ids:
                # Tạo địa điểm khai thác mặc định từ địa chỉ của partner
                self.env['dl.wood.exploitation.location'].create({
                    'partner_id': partner.id,
                    'name': _('Địa điểm chính'),
                    'street': partner.street,
                    'city': partner.city,
                    'ward_id': partner.ward_id.id if partner.ward_id else False,
                    'state_id': partner.state_id.id if partner.state_id else False,
                    'is_main': True,
                    'company_id': partner.company_id.id
                })
        return partners

    def write(self, vals):
        is_wood = any(partner.x_is_wood_supplier or partner.x_is_wood_customer for partner in self) or vals.get('x_is_wood_supplier') or vals.get('x_is_wood_customer')
        if is_wood:
            if 'company_id' in vals:
                company_id = vals.get('company_id')
                if not company_id or company_id not in self.env.companies.ids:
                    vals['company_id'] = self.env.company.id
            else:
                for partner in self:
                    if not partner.company_id or partner.company_id.id not in self.env.companies.ids:
                        vals['company_id'] = self.env.company.id
                        break
                    
        res = super(ResPartner, self).write(vals)
        for partner in self:
            if partner.x_is_wood_supplier == 'owner' and not partner.exploitation_location_ids:
                # Tạo địa điểm khai thác mặc định nếu chưa có
                self.env['dl.wood.exploitation.location'].create({
                    'partner_id': partner.id,
                    'name': _('Địa điểm chính'),
                    'street': partner.street,
                    'city': partner.city,
                    'ward_id': partner.ward_id.id if partner.ward_id else False,
                    'state_id': partner.state_id.id if partner.state_id else False,
                    'is_main': True,
                    'company_id': partner.company_id.id
                })
        return res

    @api.model
    def action_parse_cccd_address(self, raw_address):
        """
        RPC API Endpoint nhận địa chỉ thô, dùng vietnamadminunits để chuyển đổi
        địa chỉ cũ sang mới, sau đó đối chiếu với CSDL Odoo.
        """
        _logger.info("[CCCD] action_parse_cccd_address được gọi với raw_address=%r", raw_address)

        if not raw_address:
            return {}
        
        try:
            province = ""
            short_province = ""
            ward = ""
            street = ""
            
            try:
                
                # Thư viện này giúp tự động map địa chỉ cũ (có huyện) ra địa chỉ mới
                admin_unit = convert_address(raw_address)
                province = getattr(admin_unit, 'province', "") or ""
                short_province = getattr(admin_unit, 'short_province', "") or ""
                ward = getattr(admin_unit, 'ward', "") or ""
                street = getattr(admin_unit, 'street', "") or ""
            except ImportError:
                _logger.warning("[CCCD] Không tìm thấy thư viện vietnamadminunits, chuyển sang bóc tách thủ công.")
            except Exception as e:
                _logger.warning("[CCCD] Lỗi khi dùng vietnamadminunits: %s", e)
            
            # Nếu vietnamadminunits không tìm thấy tỉnh (hoặc chưa cài), áp dụng Fallback tự bóc tách bằng dấu phẩy
            if not province:
                parts = [p.strip() for p in raw_address.split(',') if p.strip()]
                if len(parts) > 1:
                    province = parts[-1]
                    short_province = province.replace("Tỉnh ", "").replace("Thành phố ", "").replace("TP ", "").replace("TP.", "").strip()
                    
                    if len(parts) >= 4:
                        ward = parts[-3]
                        district = parts[-2]
                        # Lưu lại chi tiết địa chỉ và Huyện vào street để không mất thông tin
                        street = ", ".join(parts[:-3]) + ", " + district
                    elif len(parts) == 3:
                        ward = parts[-3]
                        district = parts[-2]
                        street = district
                    elif len(parts) == 2:
                        ward = parts[-2]
                        street = ""
                else:
                    street = raw_address

            _logger.info(
                "[CCCD] Dữ liệu sẽ tìm kiếm: street=%r | ward=%r | province=%r | short_province=%r",
                street, ward, province, short_province
            )

            # Tìm ID của Tỉnh / Thành phố trong Odoo res.country.state
            state_id = False
            state_name = False
            ward_id = False
            ward_name = False

            if short_province or province:
                domain = [
                    ('country_id.code', '=', 'VN'),
                    '|',
                    ('name', '=ilike', short_province),
                    ('name', '=ilike', province)
                ]
                state = self.env['res.country.state'].search(domain, limit=1)

                if not state:
                    domain_fuzzy = [
                        ('country_id.code', '=', 'VN'),
                        '|',
                        ('name', 'ilike', '%' + short_province + '%'),
                        ('name', 'ilike', '%' + province + '%')
                    ]
                    state = self.env['res.country.state'].search(domain_fuzzy, limit=1)
                
                if state:
                    state_id = state.id
                    state_name = state.name

                    # Tiếp tục tìm ID của Xã / Phường
                    if ward:
                        ward_clean = ward.replace("Xã ", "").replace("Phường ", "").replace("Thị trấn ", "").strip()
                        ward_domain = [
                            ('state_id', '=', state_id),
                            '|',
                            ('name', '=ilike', ward),
                            ('name', '=ilike', ward_clean)
                        ]
                        ward_record = self.env['res.country.ward'].search(ward_domain, limit=1)
                        
                        if not ward_record:
                            ward_record = self.env['res.country.ward'].search([
                                ('state_id', '=', state_id),
                                ('name', 'ilike', '%' + ward_clean + '%')
                            ], limit=1)
                        
                        if ward_record:
                            ward_id = ward_record.id
                            ward_name = ward_record.name

            # Nếu fallback không ra state (do CSDL thiếu Tỉnh/Thành), ta vẫn giữ nguyên
            # street và ward đã bóc tách được ở trên, không reset lại.
            
            result = {
                'street': street or False,
                'city': ward or False,
                'state_id': state_id,
                'state_name': state_name,
                'ward_id': ward_id,
                'ward_name': ward_name,
            }
            _logger.info("[CCCD] Kết quả trả về cho frontend: %r", result)
            return result

        except Exception as e:
            # Fallback: Trả về địa chỉ gốc lưu vào street nếu thư viện lỗi
            _logger.exception("[CCCD] Exception trong action_parse_cccd_address: %s", e)
            return {
                'street': raw_address,
                'city': False,
                'state_id': False,
                'ward_id': False
            }
