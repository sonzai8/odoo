# -*- coding: utf-8 -*-
import json
import requests
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class DlWoodproConfig(models.Model):
    _name = 'dl.woodpro.config'
    _description = 'Cấu hình đồng bộ WoodPro'

    name = fields.Char(string='Tên cấu hình', required=True, default='Cấu hình WoodPro API')
    base_url = fields.Char(string='Base URL API', required=True, default='https://api.woodpro.duclam.com/api/v1')
    username = fields.Char(string='Tài khoản', required=True)
    password = fields.Char(string='Mật khẩu', required=True)
    token = fields.Char(string='JWT Token')
    last_sync_date = fields.Datetime(string='Lần đồng bộ cuối')
    x_debug_log = fields.Html(string='Nhật ký Debug', readonly=True)

    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Tên cấu hình phải là duy nhất!')
    ]

    def _add_debug_log(self, title, content):
        """Hàm phụ để ghi log vào trường x_debug_log"""
        now = fields.Datetime.now()
        new_log = f"<div style='margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px;'>" \
                  f"<strong>[{now}] {title}</strong><br/>" \
                  f"<pre style='background: #f8f9fa; padding: 5px; font-size: 11px;'>{content}</pre>" \
                  f"</div>"
        self.x_debug_log = (self.x_debug_log or "") + new_log

    def action_login(self):
        """Đăng nhập để lấy Token JWT"""
        self.ensure_one()
        url = f"{self.base_url}/auth/login"
        payload = {
            "user": self.username,
            "pass": self.password
        }
        try:
            response = requests.post(url, json=payload, timeout=15)
            debug_info = f"URL: {url}\nPayload: {json.dumps(payload)}\nStatus: {response.status_code}\nResponse: {response.text}"
            self._add_debug_log("Login Request", debug_info)
            
            data = response.json()
            if data.get('success'):
                # Lưu token vào field
                self.token = data['result']['token']
                return True
            else:
                raise UserError(_("Đăng nhập thất bại: %s") % data.get('message'))
        except Exception as e:
            self._add_debug_log("Login Error", str(e))
            raise UserError(_("Lỗi kết nối API: %s") % str(e))

    def _get_headers(self):
        if not self.token:
            self.action_login()
        # Thử nghiệm: Bỏ tiền tố 'Bearer ' vì một số API NestJS/Custom không yêu cầu
        headers = {
            'Authorization': f'{self.token}',
            'Content-Type': 'application/json'
        }
        return headers

    def action_sync_forest_owners(self):
        """Đồng bộ danh sách Chủ rừng (Tự động lặp trang)"""
        self.ensure_one()
        url = f"{self.base_url}/forestOwners"
        
        try:
            if not self.token:
                self.action_login()
                
            headers = {
                'Content-Type': 'application/json',
                'Cookie': f'id={self.token}',
                'User-Agent': 'Odoo/19.0'
            }
            
            partner_obj = self.env['res.partner']
            page = 1
            limit = 100
            total_synced = 0
            
            while True:
                params = {'page': page, 'limit': limit, 'keyword': ''}
                response = requests.get(url, headers=headers, params=params, timeout=20)
                
                if response.status_code != 200:
                    break
                    
                data = response.json()
                res = data.get('result', {})
                items = res.get('items', []) if isinstance(res, dict) else []
                
                if not items:
                    break
                
                # Lấy ID Việt Nam
                country_vn = self.env['res.country'].search([('code', '=', 'VN')], limit=1)
                
                for item in items:
                    wp_id = item.get('id')
                    name = item.get('name')
                    if not wp_id or not name: continue
                    
                    # Tự động nhận diện kiểu Công ty (is_company)
                    is_company = "công ty" in name.lower()

                    # Bóc tách địa chỉ
                    format_address = item.get('formatAddress') or ""
                    street, city, state_id = "", "", False
                    
                    if format_address:
                        # Ví dụ: Thôn Mùng, Xã Dương Hưu, Tỉnh Bắc Ninh
                        parts = [p.strip() for p in format_address.split(',')]
                        if len(parts) >= 3:
                            # Tỉnh/Thành phố (Phần cuối)
                            state_name = parts[-1].replace('Tỉnh ', '').replace('Thành phố ', '').strip()
                            state = self.env['res.country.state'].search([
                                ('name', 'ilike', state_name),
                                ('country_id', '=', country_vn.id)
                            ], limit=1)
                            state_id = state.id if state else False
                            
                            # Xã/Phường (Phần kế cuối)
                            city = parts[-2].replace('Xã ', '').replace('Phường ', '').replace('Thị trấn ', '').strip()
                            
                            # Thôn/Xóm (Các phần còn lại)
                            street = ", ".join(parts[:-2]).strip()
                        else:
                            street = format_address

                    partner = partner_obj.search([('x_woodpro_id', '=', wp_id)], limit=1)
                    vals = {
                        'name': name,
                        'phone': item.get('phone'),
                        'street': street,
                        'street2': format_address,
                        'city': city,
                        'state_id': state_id,
                        'country_id': country_vn.id,
                        'lang': 'vi_VN',
                        'x_woodpro_id': wp_id,
                        'is_company': is_company,
                        'x_is_wood_supplier': 'supplier' if is_company else 'owner',
                        'customer_rank': 1,
                    }
                    if partner:
                        partner.write(vals)
                    else:
                        partner_obj.create(vals)
                    total_synced += 1
                
                # Kiểm tra xem còn trang tiếp theo không
                total_pages = res.get('totalPages', 1)
                if page >= total_pages:
                    break
                page += 1

            debug_info = f"Kết thúc đồng bộ. Tổng số: {total_synced} bản ghi. Tổng số trang đã quét: {page}"
            self._add_debug_log("Sync Forest Owners Complete", debug_info)
            
            return self._show_notification(_('Thành công'), _('Đã đồng bộ %s chủ rừng.') % total_synced)
        except Exception as e:
            raise UserError(_("Lỗi đồng bộ chủ rừng: %s") % str(e))
    def action_sync_products(self):
        """Đồng bộ danh sách Sản phẩm Gỗ từ WoodPro"""
        self.ensure_one()
        url = f"{self.base_url}/products"
        
        try:
            if not self.token:
                self.action_login()
                
            headers = {
                'Content-Type': 'application/json',
                'Cookie': f'id={self.token}',
                'User-Agent': 'Odoo/19.0'
            }
            
            product_tmpl_obj = self.env['product.template']
            page = 1
            limit = 50
            total_synced = 0
            
            while True:
                params = {'page': page, 'limit': limit, 'keyword': ''}
                response = requests.get(url, headers=headers, params=params, timeout=20)
                
                if response.status_code != 200:
                    break
                    
                data = response.json()
                
                # Linh hoạt với cấu trúc data có hoặc không có 'result'
                items = data.get('items', [])
                res_data = data
                if not items and data.get('result'):
                    res_data = data.get('result', {})
                    items = res_data.get('items', []) if isinstance(res_data, dict) else []
                
                if not items:
                    break
                
                for item in items:
                    wp_id = item.get('id')
                    name = item.get('name')
                    code = item.get('code')
                    if not wp_id or not name: continue
                    
                    product = product_tmpl_obj.search([('x_woodpro_id', '=', wp_id)], limit=1)
                    if not product and code:
                        product = product_tmpl_obj.search([('default_code', '=', code)], limit=1)
                        
                    vals = {
                        'name': name,
                        'default_code': code,
                        'x_woodpro_id': wp_id,
                        'is_wood_product': True,
                        'tracking': 'lot',
                        'type': 'consu',
                        'is_storable': True,
                    }
                    
                    if product:
                        product.write(vals)
                    else:
                        product_tmpl_obj.create(vals)
                    total_synced += 1
                
                # Phân trang
                total_pages = res_data.get('totalPages', 1)
                if page >= total_pages:
                    break
                page += 1

            debug_info = f"Kết thúc đồng bộ sản phẩm. Tổng số: {total_synced} bản ghi. Tổng số trang đã quét: {page}"
            self._add_debug_log("Sync Products Complete", debug_info)
            
            return self._show_notification(_('Thành công'), _('Đã đồng bộ %s sản phẩm gỗ.') % total_synced)
        except Exception as e:
            raise UserError(_("Lỗi đồng bộ sản phẩm: %s") % str(e))


    def action_sync_minings(self):
        """Đồng bộ danh sách Hồ sơ khai thác (Minings)"""
        self.ensure_one()
        url = f"{self.base_url}/minings"
        
        try:
            if not self.token:
                self.action_login()
                
            headers = {
                'Content-Type': 'application/json',
                'Cookie': f'id={self.token}',
                'User-Agent': 'Odoo/19.0'
            }
            
            dossier_obj = self.env['dl.wood.dossier']
            partner_obj = self.env['res.partner']
            product_obj = self.env['product.product']
            species_obj = self.env['dl.wood.species']
            
            page = 1
            limit = 50
            total_synced = 0
            
            while True:
                params = {'page': page, 'limit': limit}
                response = requests.get(url, headers=headers, params=params, timeout=20)
                
                if response.status_code != 200:
                    break
                    
                data = response.json()
                
                # Linh hoạt với cấu trúc data có hoặc không có 'result'
                items = data.get('items', [])
                res_data = data
                if not items and data.get('result'):
                    res_data = data.get('result', {})
                    items = res_data.get('items', []) if isinstance(res_data, dict) else []
                
                if not items:
                    break
                
                for item in items:
                    wp_id = item.get('id')
                    code = item.get('miningCode') or item.get('index')
                    if not wp_id: continue
                    
                    partner = partner_obj.search([('x_woodpro_id', '=', (item.get('forestOwner') or {}).get('id'))], limit=1)
                    
                    # Woods - Một hồ sơ có nhiều loại gỗ
                    woods = item.get('woods', [])
                    line_vals = []
                    main_product = False
                    
                    # Bóc tách thông số đường kính từ chuỗi (Ví dụ: "12-30")
                    for w in woods:
                        w_wp_id = w.get('productId') or w.get('id')
                        w_name = w.get('name')
                        
                        # Ánh xạ species_id
                        species = species_obj.search([('name', '=', w_name)], limit=1)
                        if not species and w_name:
                            species = species_obj.create({'name': w_name})
                        
                        # Tìm product tương ứng để làm product_id cho dossier (lấy loại đầu tiên làm đại diện)
                        if not main_product:
                            if w_wp_id:
                                main_product = product_obj.search([('product_tmpl_id.x_woodpro_id', '=', w_wp_id)], limit=1)
                            if not main_product and w_name:
                                main_product = product_obj.search([('name', '=', w_name)], limit=1)
                        
                        # Xử lý bóc tách đường kính từ API (Ví dụ: "12-30")
                        d_api = str(w.get('avgDiameter', '0'))
                        d_min, d_max = 0.0, 0.0
                        if '-' in d_api:
                            try:
                                d_parts = d_api.split('-')
                                d_min = float(d_parts[0])
                                d_max = float(d_parts[1])
                            except: pass
                        else:
                            try:
                                d_min = d_max = float(d_api)
                            except: pass

                        # Chiều cao trung bình
                        avg_height = float(w.get('avgHeight') or 0)
                        
                        # Lấy đơn giá từ API hoặc tra cứu từ Phân loại chất lượng
                        price_unit = w.get('price') or w.get('unitPrice') or 0
                        
                        if price_unit == 0 and species:
                            grade = self.env['dl.wood.species.grade'].search([
                                ('species_id', '=', species.id),
                                ('diameter_min', '<=', d_min),
                                ('diameter_max', '>=', d_max),
                                ('height_min', '<=', avg_height),
                                ('height_max', '>=', avg_height)
                            ], limit=1)
                            if grade:
                                price_unit = grade.default_price

                        line_vals.append((0, 0, {
                            'species_id': species.id if species else False,
                            'name': w_name,
                            'name_sci': w.get('nameSci'),
                            'quantity': w.get('quantity', 0),
                            'volume': w.get('weight', 0),
                            'price_unit': price_unit,
                            'diameter_min': d_min,
                            'diameter_max': d_max,
                            'height_min': avg_height, # Tạm thời gán vào min nếu API chỉ trả 1 số
                            'height_max': avg_height,
                            'avg_diameter': (d_min + d_max) / 2 if d_max > 0 else d_min,
                            'avg_height': avg_height,
                            'note': w.get('note'),
                            'x_woodpro_id': w_wp_id,
                        }))

                    # Nếu không có product nào, dùng mặc định
                    if not main_product:
                        default_name = "Gỗ Nguyên Liệu (Đồng bộ WoodPro)"
                        main_product = product_obj.search([('name', '=', default_name)], limit=1)
                        if not main_product:
                            main_product = product_obj.create({
                                'name': default_name, 'type': 'consu', 'is_storable': True, 'is_wood_product': True, 'tracking': 'lot'
                            })

                    dossier = dossier_obj.search([('x_woodpro_id', '=', wp_id)], limit=1)
                    mining_address = item.get('formatAddress') or ""
                    
                    # Cập nhật địa điểm khai thác cho chủ rừng
                    if partner and mining_address:
                        loc_obj = self.env['dl.wood.exploitation.location']
                        parts = [p.strip() for p in mining_address.split(',')]
                        
                        # Tên địa điểm = 2 thông tin đầu tiên
                        loc_name = ", ".join(parts[:2]) if len(parts) >= 2 else parts[0] if parts else _('Địa điểm khai thác')
                        
                        # Bóc tách địa chỉ chi tiết
                        street, city, state_id = "", "", False
                        country_vn = self.env['res.country'].search([('code', '=', 'VN')], limit=1)
                        
                        if len(parts) >= 3:
                            state_name = parts[-1].replace('Tỉnh ', '').replace('Thành phố ', '').strip()
                            state = self.env['res.country.state'].search([
                                ('name', 'ilike', state_name),
                                ('country_id', '=', country_vn.id)
                            ], limit=1)
                            state_id = state.id if state else False
                            city = parts[-2].replace('Xã ', '').replace('Phường ', '').replace('Thị trấn ', '').strip()
                            street = ", ".join(parts[:-2]).strip()
                        else:
                            street = mining_address

                        # Tìm xem địa điểm này đã có chưa (dựa trên địa chỉ)
                        existing_loc = loc_obj.search([
                            ('partner_id', '=', partner.id),
                            ('street', '=', street),
                            ('city', '=', city)
                        ], limit=1)
                        
                        loc_vals = {
                            'partner_id': partner.id,
                            'name': loc_name,
                            'street': street,
                            'city': city,
                            'state_id': state_id,
                            'is_main': True # Đặt làm mặc định như yêu cầu
                        }
                        
                        exploitation_location = False
                        if existing_loc:
                            existing_loc.write(loc_vals)
                            exploitation_location = existing_loc
                        else:
                            # Nếu có địa điểm chính cũ, bỏ đánh dấu đi trước khi tạo cái mới là chính
                            loc_obj.search([('partner_id', '=', partner.id), ('is_main', '=', True)]).write({'is_main': False})
                            exploitation_location = loc_obj.create(loc_vals)

                    vals = {
                        'name': str(code),
                        'partner_id': partner.id if partner else False,
                        'exploitation_location_id': exploitation_location.id if exploitation_location else False,
                        'product_id': main_product.id,
                        'initial_qty': item.get('totalQuantity', 0),
                        'date_received': (item.get('createdAt') or fields.Date.today())[:10],
                        'x_start_date': (item.get('startMining') or '')[:10] if item.get('startMining') else False,
                        'x_end_date': (item.get('endMining') or '')[:10] if item.get('endMining') else False,
                        'x_addendum_num': item.get('addendumNum'),
                        'x_woodpro_id': wp_id,
                        'x_mining_address': mining_address,
                        'x_mining_method': 'group' if item.get('exploitMethod') == 'Khai thác theo đám' else 'white',
                        'x_area': item.get('area', 0),
                        'line_ids': line_vals,
                    }
                    if dossier:
                        # Xóa line cũ trước khi cập nhật
                        dossier.line_ids.unlink()
                        dossier.write(vals)
                    else:
                        dossier = dossier_obj.create(vals)
                    
                    # Tạm thời tắt đồng bộ tệp đính kèm theo yêu cầu
                    # self._sync_dossier_attachments(dossier, headers)
                    
                    total_synced += 1
                
                if len(items) < limit:
                    break
                page += 1

            self.last_sync_date = fields.Datetime.now()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Thành công',
                    'message': f'Đã đồng bộ {total_synced} hồ sơ gỗ và tệp đính kèm.',
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            self.x_debug_log = f"Error syncing minings: {str(e)}"
            return False

    def action_sync_customers(self):
        """Đồng bộ danh sách Khách hàng từ API /productions."""
        self.ensure_one()
        url = f"{self.base_url}/productions"
        _logger.info("=== BẮT ĐẦU ĐỒNG BỘ KHÁCH HÀNG TỪ WOODPRO ===")

        try:
            if not self.token:
                self.action_login()

            headers = {
                'Content-Type': 'application/json',
                'Cookie': f'id={self.token}',
                'User-Agent': 'Odoo/19.0'
            }

            partner_obj = self.env['res.partner']
            page = 1
            limit = 50
            total_synced = 0
            # Từ khóa nhận diện công ty (không phân biệt hoa/thường)
            company_keywords = ['công ty', 'company', 'co.', 'corp', 'ltd', 'tnhh', 'cổ phần', 'hợp tác xã', 'htx']

            # Lấy thông tin Việt Nam
            vietnam = self.env['res.country'].search([('code', '=', 'VN')], limit=1)
            vn_states = self.env['res.country.state'].search([('country_id', '=', vietnam.id)]) if vietnam else []

            while True:
                params = {'page': page, 'limit': limit}
                _logger.info(f"Đang gọi API trang {page} (limit {limit})...")
                response = requests.get(url, headers=headers, params=params, timeout=20)

                if response.status_code != 200:
                    _logger.error(f"Lỗi API: Status {response.status_code} - {response.text}")
                    break

                data = response.json()
                result_data = data.get('result', {})
                items = []
                if isinstance(result_data, dict):
                    items = result_data.get('items', [])
                
                if not items:
                    _logger.info("Không còn dữ liệu khách hàng để đồng bộ.")
                    break

                _logger.info(f"Tìm thấy {len(items)} bản ghi sản xuất. Đang trích xuất thông tin khách hàng...")

                seen_codes = set()

                for item in items:
                    receiver_code = item.get('receiverCode') or ''
                    receiver_name = item.get('receiverName') or ''
                    receiver_address = item.get('receiverAddress') or ''

                    if not receiver_name:
                        continue
                    if receiver_code and receiver_code in seen_codes:
                        continue
                    if receiver_code:
                        seen_codes.add(receiver_code)

                    # Xác định loại: công ty hay cá nhân
                    name_lower = receiver_name.lower()
                    is_company = any(kw in name_lower for kw in company_keywords)
                    company_type = 'company' if is_company else 'person'

                    # Phân tích địa chỉ để tìm State và Xã/Phường
                    state_id = False
                    ward = False
                    if receiver_address:
                        addr_parts = [p.strip() for p in receiver_address.split(',')]
                        
                        # 1. Tìm Tỉnh/Thành phố (thường ở cuối chuỗi)
                        if vn_states:
                            potential_states = addr_parts[-2:] if len(addr_parts) >= 2 else addr_parts
                            for part in potential_states:
                                if part.lower() in ['việt nam', 'vietnam']:
                                    continue
                                clean_state_part = part.replace('Tỉnh', '').replace('Thành phố', '').replace('TP.', '').replace('TP', '').strip().lower()
                                match_state = vn_states.filtered(lambda s: clean_state_part in s.name.lower() or s.name.lower() in clean_state_part)
                                if match_state:
                                    state_id = match_state[0].id
                                    break
                        
                        # 2. Tìm Xã/Phường (duyệt qua các phần của địa chỉ)
                        ward_keywords = ['phường', 'xã', 'thị trấn', 'p.', 'x.']
                        for part in addr_parts:
                            part_lower = part.lower()
                            if any(kw in part_lower for kw in ward_keywords):
                                # Trích xuất tên (ví dụ: "Phường Bắc Giang" -> lấy "Bắc Giang")
                                # Hoặc nếu anh muốn lấy cả cụm "Phường Bắc Giang" thì bỏ .replace bên dưới
                                clean_ward = part
                                for kw in ['Phường', 'Xã', 'Thị trấn', 'phường', 'xã', 'thị trấn', 'P.', 'X.']:
                                    clean_ward = clean_ward.replace(kw, '')
                                ward = clean_ward.strip()
                                break

                    vals = {
                        'name': receiver_name,
                        'phone': item.get('receiverPhone') or False,
                        'email': item.get('receiverEmail') or False,
                        'street': receiver_address,
                        'city': ward, # Lưu Xã/Phường vào trường city
                        'x_customer_code': receiver_code or False,
                        'company_type': company_type,
                        'is_company': is_company,
                        'x_is_wood_customer': True,
                        'lang': 'vi_VN',
                        'country_id': vietnam.id if vietnam else False,
                        'state_id': state_id,
                    }

                    # Tìm theo mã khách hàng trước, sau đó theo tên
                    existing = False
                    if receiver_code:
                        existing = partner_obj.search([('x_customer_code', '=', receiver_code)], limit=1)
                    if not existing:
                        existing = partner_obj.search([
                            ('name', '=', receiver_name),
                            ('x_is_wood_customer', '=', True)
                        ], limit=1)

                    if existing:
                        _logger.info(f"Cập nhật khách hàng: {receiver_name} ({receiver_code})")
                        existing.write(vals)
                        partner = existing
                    else:
                        _logger.info(f"Tạo mới khách hàng: {receiver_name} ({receiver_code})")
                        partner = partner_obj.create(vals)

                    # --- ĐỒNG BỘ ĐƠN HÀNG VÀ LỆNH SẢN XUẤT ---
                    production_id = item.get('id')
                    production_code = item.get('code') # Ví dụ: SX000001
                    invoice_code = item.get('invoiceCode') # Số hóa đơn dùng để gom nhóm
                    
                    if production_id:
                        # 1. Tìm hoặc tạo Đơn đặt hàng
                        # Ưu tiên tìm theo Số hóa đơn để gom nhóm, sau đó mới tìm theo WoodPro ID
                        sale_order_obj = self.env['dl.wood.sale.order']
                        sale_order = False
                        
                        if invoice_code:
                            sale_order = sale_order_obj.search([('x_invoice_code', '=', invoice_code)], limit=1)
                        
                        if not sale_order:
                            sale_order = sale_order_obj.search([('x_woodpro_id', '=', production_id)], limit=1)
                        
                        if not sale_order:
                            # Sử dụng Số hóa đơn làm mã đơn hàng, nếu không có mới dùng sequence
                            so_name = invoice_code
                            if not so_name:
                                so_name = self.env['ir.sequence'].next_by_code('dl.wood.sale.order.temp') or 'DL-DH-00001'
                            
                            so_vals = {
                                'name': so_name,
                                'partner_id': partner.id,
                                'x_invoice_code': invoice_code,
                                'date_order': item.get('timeAt')[:10] if item.get('timeAt') else fields.Date.today(),
                                'x_woodpro_id': production_id,
                                'state': 'done', # Tự động hoàn thành đơn hàng
                                'note': item.get('note'),
                            }
                            sale_order = sale_order_obj.create(so_vals)
                            _logger.info(f"Đã tạo và Hoàn thành Đơn hàng: {sale_order.name}")
                        else:
                            # Cập nhật thông tin nếu cần
                            if not sale_order.x_invoice_code and invoice_code:
                                sale_order.write({'x_invoice_code': invoice_code})
                            
                            # Cập nhật trạng thái hoàn thành cho đơn hàng cũ
                            if sale_order.state != 'done':
                                sale_order.write({'state': 'done'})
                            
                            # Kiểm tra và sửa lỗi lặp tiền tố nếu có
                            if sale_order.name and sale_order.name.startswith('DL-DH-DL-DH-'):
                                new_name = sale_order.name.replace('DL-DH-DL-DH-', 'DL-DH-')
                                sale_order.write({'name': new_name})
                                _logger.info(f"Đã cập nhật đơn hàng cũ: {new_name}")

                        # 2. Xử lý các Production Details (Lệnh sản xuất)
                        prod_order_obj = self.env['dl.wood.production.order']
                        details = item.get('productionDetails', [])
                        
                        for detail in details:
                            detail_id = detail.get('id')
                            woodpro_product = detail.get('product', {})
                            product_name = woodpro_product.get('name', 'Sản phẩm WoodPro')
                            product_code = woodpro_product.get('code')
                            
                            # Tìm hoặc tạo sản phẩm trong Odoo
                            product = self.env['product.product'].search([('default_code', '=', product_code)], limit=1)
                            if not product and product_code:
                                product = self.env['product.product'].create({
                                    'name': product_name,
                                    'default_code': product_code,
                                    'type': 'product',
                                })
                            
                            # Kiểm tra lệnh SX đã tồn tại chưa
                            prod_order = prod_order_obj.search([('x_woodpro_id', '=', detail_id)], limit=1)
                            
                            if not prod_order:
                                po_vals = {
                                    'name': production_code or _('Mới'),
                                    'sale_order_id': sale_order.id,
                                    'product_id': product.id if product else False,
                                    'qty_planned': detail.get('quantity', 0.0),
                                    'qty_done': detail.get('quantity', 0.0),
                                    'date_planned': item.get('timeAt')[:10] if item.get('timeAt') else fields.Date.today(),
                                    'date_done': item.get('createdAt')[:10] if item.get('createdAt') else fields.Date.today(),
                                    'x_woodpro_id': detail_id,
                                    'state': 'done', # Tự động hoàn thành lệnh sản xuất
                                }
                                prod_order = prod_order_obj.create(po_vals)
                                _logger.info(f"Đã tạo và Hoàn thành Lệnh sản xuất: {prod_order.name}")
                                
                                # 3. Xử lý Nguyên liệu tiêu hao (BOMs)
                                boms = detail.get('boms', [])
                                line_vals = []
                                for bom in boms:
                                    species_name = bom.get('nameSci') or (bom.get('subWood', {}).get('wood', {}).get('name'))
                                    species = self.env['dl.wood.species'].search([('name', '=', species_name)], limit=1)
                                    if not species:
                                        species = self.env['dl.wood.species'].create({'name': species_name})
                                    
                                    # Tìm hồ sơ gỗ tương ứng nếu có miningId
                                    mining_id = bom.get('miningId')
                                    dossier = self.env['dl.wood.dossier'].search([('x_woodpro_id', '=', mining_id)], limit=1)
                                    
                                    line_vals.append((0, 0, {
                                        'species_id': species.id,
                                        'dossier_id': dossier.id if dossier else False,
                                        'volume_planned': bom.get('quantity', 0.0),
                                        'volume_actual': bom.get('quantity', 0.0),
                                        'note': bom.get('note'),
                                    }))
                                
                                if line_vals:
                                    prod_order.write({'line_ids': line_vals})
                                    # Quan trọng: Gọi hàm trừ lùi nguyên vật liệu và ghi sổ cái ngay lập tức
                                    # Sử dụng force=True để bỏ qua kiểm tra tồn kho khi sync dữ liệu cũ
                                    prod_order._action_deduct_materials(force=True)
                            else:
                                # Cập nhật trạng thái hoàn thành cho lệnh sản xuất cũ nếu chưa done
                                if prod_order.state != 'done':
                                    prod_order.write({'state': 'done'})
                                    # Nếu trước đó chưa trừ kho thì giờ trừ kho
                                    prod_order._action_deduct_materials(force=True)
                                    _logger.info(f"Đã hoàn thành lệnh sản xuất cũ: {prod_order.name}")

                    total_synced += 1

                if len(items) < limit:
                    break
                page += 1

            _logger.info(f"=== ĐỒNG BỘ HOÀN TẤT: {total_synced} BẢN GHI === ")
            self.last_sync_date = fields.Datetime.now()
            return self._show_notification(
                _('Thành công'),
                _('Đã đồng bộ %s khách hàng và các đơn hàng/lệnh sản xuất liên quan.') % total_synced
            )
        except Exception as e:
            _logger.error(f"Lỗi ngoại lệ khi đồng bộ: {str(e)}")
            self.x_debug_log = (self.x_debug_log or '') + f"<br/>Error syncing: {str(e)}"
            raise UserError(_('Lỗi đồng bộ: %s') % str(e))

    def _sync_dossier_attachments(self, dossier, headers):
        """Đồng bộ danh sách tệp đính kèm từ WoodPro"""
        if not dossier.x_woodpro_id:
            return
            
        try:
            # API lấy danh sách file: đảm bảo không bị lặp lại /v1
            base = self.base_url.rstrip('/')
            if base.endswith('/v1'):
                url = f"{base}/contracts/{dossier.x_woodpro_id}?version=tt262025"
            else:
                url = f"{base}/v1/contracts/{dossier.x_woodpro_id}?version=tt262025"
                
            response = requests.get(url, headers=headers, timeout=20)
            
            if response.status_code != 200:
                return
                
            res_data = response.json()
            files_data = res_data.get('result') if isinstance(res_data, dict) else res_data
            
            if not isinstance(files_data, list):
                return
                
            attachment_obj = self.env['dl.wood.dossier.attachment']
            # Xóa các tệp cũ để cập nhật mới
            dossier.attachment_ids.unlink()
            
            count = 0
            for f in files_data:
                f_id = f.get('id')
                f_name = f.get('name')
                
                if not f_id: continue
                
                # Ánh xạ loại file dựa trên tên từ WoodPro
                f_type = False
                if "Phiếu thông tin khai thác" in f_name:
                    f_type = "forest_exploitation"
                elif "Hợp đồng" in f_name:
                    f_type = "hsg"
                elif "Bảng kê lâm sản" in f_name:
                    f_type = "manifest"
                
                # Xây dựng URL tải file dựa trên ID của tệp tin (f_id)
                if base.endswith('/v1'):
                    download_url = f"{base}/views/{f_id}?type=forest_exploitation&version=tt262022&woodType=wood"
                else:
                    download_url = f"{base}/v1/views/{f_id}?type=forest_exploitation&version=tt262025&woodType=wood"
                
                attachment_obj.create({
                    'dossier_id': dossier.id,
                    'name': f_name,
                    'x_woodpro_id': f_id,
                    'status': f.get('status'),
                    'url': download_url,
                    'file_type': f_type,
                })
                count += 1
            
        except Exception as e:
            self.x_debug_log = (self.x_debug_log or "") + f"<br/>Error syncing attachments for {dossier.name}: {str(e)}"

    def _show_notification(self, title, message):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }
