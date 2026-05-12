# -*- coding: utf-8 -*-
import json
import requests
import re
import logging
from odoo import models, fields, api, _, tools
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
    
    x_sync_mode = fields.Selection([
        ('update', 'Cập nhật (Chỉ bổ sung mới)'),
        ('overwrite', 'Ghi đè (Làm mới dữ liệu đã tồn tại)')
    ], string='Chế độ đồng bộ', default='update', required=True)

    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Tên cấu hình phải là duy nhất!')
    ]

    def _safe_float(self, value, default=0.0, field_name=""):
        """Chuyển đổi sang float an toàn và ghi log chi tiết"""
        if not value:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        
        val_str = str(value).strip().replace(',', '.')
        try:
            for sep in ['-', '–', '—']:
                if sep in val_str:
                    parts = [p.strip() for p in val_str.split(sep) if p.strip()]
                    if len(parts) >= 2:
                        res = (float(parts[0]) + float(parts[1])) / 2
                        _logger.info(f"SafeFloat: Bóc tách khoảng '{val_str}' -> {res} (Trường: {field_name})")
                        return res
                    elif len(parts) == 1:
                        return float(parts[0])
            num_match = re.search(r"[-+]?\d*\.?\d+", val_str)
            if num_match:
                res = float(num_match.group())
                return res
        except Exception as e:
            msg = f"Lỗi SafeFloat tại trường '{field_name}': Không thể chuyển đổi '{val_str}' - {str(e)}"
            _logger.warning(msg)
            self._add_debug_log("Cảnh báo dữ liệu số", msg)
        return default

    def _add_debug_log(self, title, content):
        now = fields.Datetime.now()
        new_log = f"<div style='margin-bottom: 8px; border-bottom: 1px solid #ddd; padding-bottom: 4px;'>" \
                  f"<span style='color: #666; font-size: 10px;'>[{now}]</span> " \
                  f"<strong style='color: #d9534f;'>{title}</strong>: {content}" \
                  f"</div>"
        current_log = (self.x_debug_log or "")
        if len(current_log) > 50000:
            current_log = current_log[:20000] + "...(Đã cắt bớt log cũ)..."
        self.x_debug_log = new_log + current_log

    def _safe_datetime(self, date_str):
        """Chuyển đổi chuỗi ngày tháng từ API WoodPro sang đối tượng datetime Odoo"""
        if not date_str:
            return False
        try:
            # WoodPro format: 2025-12-05T00:00:00.000Z
            # Odoo yêu cầu YYYY-MM-DD HH:MM:SS (thay T bằng khoảng trắng)
            clean_str = date_str.replace('Z', '').split('.')[0].replace('T', ' ')
            return fields.Datetime.to_datetime(clean_str)
        except Exception as e:
            _logger.warning(f"WOODPRO: Không thể convert ngày tháng '{date_str}': {str(e)}")
            return False

    def _extract_dimensions(self, name):
        if not name: return 0.0, 0.0, 0.0
        pattern = r'(\d+(?:\.\d+)?)\s*mm\s*[xX*]\s*(\d+(?:\.\d+)?)\s*mm\s*[xX*]\s*(\d+(?:\.\d+)?)\s*mm'
        match = re.search(pattern, name, re.IGNORECASE)
        if match:
            try: return float(match.group(1)), float(match.group(2)), float(match.group(3))
            except: pass
        return 0.0, 0.0, 0.0

    def action_login(self):
        self.ensure_one()
        url = f"{self.base_url}/auth/login"
        payload = {"user": self.username, "pass": self.password}
        try:
            response = requests.post(url, json=payload, timeout=15)
            data = response.json()
            if data.get('success'):
                self.token = data['result']['token']
                return True
            else:
                raise UserError(_("Đăng nhập thất bại: %s") % data.get('message'))
        except Exception as e:
            raise UserError(_("Lỗi kết nối API: %s") % str(e))

    def action_sync_forest_owners(self):
        self.ensure_one()
        url = f"{self.base_url}/forestOwners"
        try:
            if not self.token: self.action_login()
            headers = {'Content-Type': 'application/json', 'Cookie': f'id={self.token}', 'User-Agent': 'Odoo/19.0'}
            partner_obj = self.env['res.partner']
            page, limit, total_synced = 1, 100, 0
            country_vn = self.env['res.country'].search([('code', '=', 'VN')], limit=1)
            vn_states = self.env['res.country.state'].search([('country_id', '=', country_vn.id)]) if country_vn else []
            while True:
                response = requests.get(url, headers=headers, params={'page': page, 'limit': limit}, timeout=20)
                if response.status_code != 200: break
                data = response.json()
                res = data.get('result', {})
                items = res.get('items', []) if isinstance(res, dict) else []
                if not items: break
                for item in items:
                    wp_id, name = item.get('id'), item.get('name')
                    if not wp_id or not name: continue
                    is_company = "công ty" in name.lower() or "tnhh" in name.lower()
                    format_address = item.get('formatAddress') or ""
                    street, city, state_id = format_address, "", False
                    if format_address:
                        parts = [p.strip() for p in format_address.split(',')]
                        if len(parts) >= 3:
                            state_name = parts[-1].replace('Tỉnh ', '').replace('Thành phố ', '').replace('TP ', '').strip()
                            state = vn_states.filtered(lambda s: state_name.lower() in s.name.lower() or s.name.lower() in state_name.lower())
                            state_id = state[0].id if state else False
                            city = parts[-2].replace('Xã ', '').replace('Phường ', '').replace('Thị trấn ', '').strip()
                            street = ", ".join(parts[:-2]).strip()
                    partner = partner_obj.search([('x_woodpro_id', '=', wp_id)], limit=1)
                    vals = {
                        'name': name, 'phone': item.get('phone'), 'street': street, 'street2': format_address,
                        'city': city, 'state_id': state_id, 'country_id': country_vn.id, 'lang': 'vi_VN',
                        'x_woodpro_id': wp_id, 'is_company': is_company, 'x_is_wood_supplier': 'supplier' if is_company else 'owner'
                    }
                    if partner: partner.write(vals)
                    else: partner_obj.create(vals)
                    total_synced += 1
                if page >= res.get('totalPages', 1): break
                page += 1
            return self._show_notification(_('Thành công'), _('Đã đồng bộ %s chủ rừng.') % total_synced)
        except Exception as e:
            raise UserError(_("Lỗi đồng bộ chủ rừng: %s") % str(e))

    def action_sync_products(self):
        self.ensure_one()
        url = f"{self.base_url}/products"
        try:
            if not self.token: self.action_login()
            headers = {'Content-Type': 'application/json', 'Cookie': f'id={self.token}', 'User-Agent': 'Odoo/19.0'}
            product_tmpl_obj = self.env['product.template']
            page, limit, total_synced = 1, 50, 0
            while True:
                response = requests.get(url, headers=headers, params={'page': page, 'limit': limit}, timeout=20)
                if response.status_code != 200: break
                data = response.json()
                res_data = data.get('result', data) if isinstance(data.get('result'), dict) else data
                items = res_data.get('items', [])
                if not items: break
                for item in items:
                    wp_id, name, code = item.get('id'), item.get('name'), item.get('code')
                    if not wp_id or not name: continue
                    product = product_tmpl_obj.search([('x_woodpro_id', '=', wp_id)], limit=1)
                    clean_code = code.replace(' ', '') if code else ''
                    thickness, width, length = self._extract_dimensions(name)
                    vals = {
                        'name': name, 'default_code': clean_code, 'x_woodpro_id': wp_id, 'is_wood_product': True,
                        'tracking': 'lot', 'type': 'consu', 'is_storable': True, 'x_thickness': thickness,
                        'x_width': width, 'x_length': length,
                    }
                    if clean_code and '-' in clean_code:
                        try: vals['list_price'] = self._safe_float(clean_code.split('-')[1], field_name="Giá") * 1000000
                        except: pass
                    if clean_code and '_' in clean_code:
                        try:
                            uom_part = clean_code.split('_')[1]
                            uom_char = uom_part[0].upper() if uom_part else ''
                            uom_name = 'Tấm' if uom_char == 'T' else 'm³' if uom_char == 'M' else False
                            if uom_name:
                                uom = self.env['uom.uom'].search([('name', 'ilike', uom_name)], limit=1)
                                if not uom and uom_name == 'm³': uom = self.env['uom.uom'].search([('name', 'ilike', 'm3')], limit=1)
                                if uom: vals['uom_id'] = uom.id
                        except: pass
                    if product: product.write(vals)
                    else: product_tmpl_obj.create(vals)
                    total_synced += 1
                if page >= res_data.get('totalPages', 1): break
                page += 1
            return self._show_notification(_('Thành công'), _('Đã đồng bộ %s thành phẩm.') % total_synced)
        except Exception as e:
            raise UserError(_("Lỗi đồng bộ sản phẩm: %s") % str(e))

    def action_sync_minings(self):
        self.ensure_one()
        url = f"{self.base_url}/minings"
        try:
            if not self.token: self.action_login()
            headers = {'Content-Type': 'application/json', 'Cookie': f'id={self.token}', 'User-Agent': 'Odoo/19.0'}
            dossier_obj = self.env['dl.wood.dossier']
            partner_obj = self.env['res.partner']
            product_obj = self.env['product.product']
            species_obj = self.env['dl.wood.species']
            loc_obj = self.env['dl.wood.exploitation.location']
            country_vn = self.env['res.country'].search([('code', '=', 'VN')], limit=1)
            page, limit, total_synced = 1, 50, 0
            while True:
                response = requests.get(url, headers=headers, params={'page': page, 'limit': limit}, timeout=20)
                if response.status_code != 200: break
                data = response.json()
                res_data = data.get('result', data) if isinstance(data.get('result'), dict) else data
                items = res_data.get('items', [])
                if not items: break
                for item in items:
                    wp_id = item.get('id')
                    code = item.get('miningCode') or item.get('index')
                    if not wp_id: continue
                    _logger.info(f"Đồng bộ HSG ID: {wp_id}")
                    partner = partner_obj.search([('x_woodpro_id', '=', (item.get('forestOwner') or {}).get('id'))], limit=1)
                    mining_address = item.get('formatAddress') or ""
                    exploitation_location = False
                    if partner and mining_address:
                        parts = [p.strip() for p in mining_address.split(',')]
                        street, city, state_id = mining_address, "", False
                        if len(parts) >= 3:
                            state_name = parts[-1].replace('Tỉnh ', '').replace('Thành phố ', '').strip()
                            state = self.env['res.country.state'].search([('name', 'ilike', state_name), ('country_id', '=', country_vn.id)], limit=1)
                            state_id = state.id if state else False
                            city = parts[-2].replace('Xã ', '').replace('Phường ', '').replace('Thị trấn ', '').strip()
                            street = ", ".join(parts[:-2]).strip()
                        existing_loc = loc_obj.search([('partner_id', '=', partner.id), ('street', '=', street), ('city', '=', city)], limit=1)
                        loc_vals = {'partner_id': partner.id, 'name': parts[0], 'street': street, 'city': city, 'state_id': state_id}
                        if existing_loc: existing_loc.write(loc_vals); exploitation_location = existing_loc
                        else: exploitation_location = loc_obj.create(loc_vals)
                    woods = item.get('woods', [])
                    line_vals, main_product = [], False
                    for w in woods:
                        w_name = w.get('name')
                        species = species_obj.search([('name', '=', w_name)], limit=1)
                        if not species and w_name: species = species_obj.create({'name': w_name})
                        if not main_product:
                            main_product = product_obj.search([('product_tmpl_id.x_woodpro_id', '=', w.get('productId'))], limit=1)
                            if not main_product: main_product = product_obj.search([('name', '=', w_name)], limit=1)
                        d_val = self._safe_float(w.get('avgDiameter', '0'), field_name="ĐK")
                        h_val = self._safe_float(w.get('avgHeight', '0'), field_name="Cao")
                        line_vals.append((0, 0, {
                            'species_id': species.id if species else False, 'name': w_name, 'name_sci': w.get('nameSci'),
                            'quantity': self._safe_float(w.get('quantity', 0), field_name="SL"), 
                            'volume': self._safe_float(w.get('weight', 0), field_name="KL"), 
                            'price_unit': self._safe_float(w.get('price') or w.get('unitPrice') or 0, field_name="Giá"),
                            'diameter_min': d_val, 'diameter_max': d_val, 'avg_height': h_val,
                            'x_woodpro_id': w.get('productId') or w.get('id'),
                        }))
                    if not main_product:
                        main_product = product_obj.search([('name', '=', "Gỗ Nguyên Liệu")], limit=1)
                        if not main_product: main_product = product_obj.create({'name': "Gỗ Nguyên Liệu", 'type': 'consu', 'is_storable': True, 'is_wood_product': True})
                    dossier = dossier_obj.search([('x_woodpro_id', '=', wp_id)], limit=1)
                    if not dossier or self.x_sync_mode == 'overwrite':
                        vals = {
                            'name': str(code), 'partner_id': partner.id if partner else False, 'product_id': main_product.id,
                            'exploitation_location_id': exploitation_location.id if exploitation_location else False,
                            'initial_qty': self._safe_float(item.get('totalQuantity', 0), field_name="Tổng HSG"), 
                            'date_received': (item.get('createdAt') or fields.Date.today())[:10],
                            'x_woodpro_id': wp_id, 'x_mining_address': mining_address, 'line_ids': line_vals,
                        }
                        if not dossier: dossier = dossier_obj.create(vals)
                        else: dossier.line_ids.unlink(); dossier.write(vals)

                        # Logic tự động chuyển trạng thái dựa trên tồn kho thực tế
                        if dossier.remaining_qty < 3.0:
                            dossier.write({'state': 'closed'})
                        else:
                            dossier.write({'state': 'in_use'})
                    self._sync_dossier_attachments(dossier, headers)
                    total_synced += 1
                if page >= res_data.get('totalPages', 1): break
                page += 1
            return self._show_notification(_('Thành công'), _('Đã đồng bộ %s hồ sơ gỗ.') % total_synced)
        except Exception as e:
            _logger.error("Lỗi đồng bộ hồ sơ gỗ: %s", str(e), exc_info=True)
            self._add_debug_log("Lỗi đồng bộ hồ sơ gỗ", str(e))
            raise UserError(_("Lỗi đồng bộ hồ sơ gỗ: %s") % str(e))

    def action_sync_customers(self):
        self.ensure_one()
        url = f"{self.base_url}/productions"
        try:
            if not self.token: self.action_login()
            headers = {'Content-Type': 'application/json', 'Cookie': f'id={self.token}', 'User-Agent': 'Odoo/19.0'}
            partner_obj = self.env['res.partner']
            sale_order_obj = self.env['dl.wood.sale.order']
            prod_order_obj = self.env['dl.wood.production.order']
            prod_line_obj = self.env['dl.wood.production.product.line']
            species_obj = self.env['dl.wood.species']
            page, limit, total_synced = 1, 50, 0
            with tools.mute_logger('odoo.models.unlink'):
                while True:
                    response = requests.get(url, headers=headers, params={'page': page, 'limit': limit}, timeout=20)
                    if response.status_code != 200: break
                    data = response.json()
                    items = data.get('result', {}).get('items', [])
                    if not items: break
                    for item in items:
                        receiver_name = item.get('receiverName')
                        if not receiver_name: continue
                        production_id, production_code, invoice_code = item.get('id'), item.get('code'), item.get('invoiceCode')
                        _logger.debug(f"Đồng bộ đơn hàng WoodPro ID: {production_id}")
                        
                        partner = partner_obj.search([('name', '=', receiver_name)], limit=1)
                        if not partner:
                            partner = partner_obj.create({
                                'name': receiver_name, 
                                'phone': item.get('receiverPhone'), 
                                'x_is_wood_customer': True
                            })
                        
                        sale_order = sale_order_obj.search([('x_woodpro_id', '=', production_id)], limit=1)
                        if not sale_order:
                            sale_order = sale_order_obj.create({
                                'name': invoice_code or f"TEMP-{production_id}", 
                                'partner_id': partner.id,
                                'date_order': (item.get('createdAt') or fields.Date.today())[:10],
                                'x_invoice_code': invoice_code, 
                                'x_woodpro_id': production_id, 
                                'state': 'done'
                            })
                        elif self.x_sync_mode == 'overwrite':
                            sale_order.write({
                                'date_order': (item.get('createdAt') or fields.Date.today())[:10]
                            })
                        
                        prod_order = prod_order_obj.search([('x_woodpro_id', '=', production_id)], limit=1)
                        order_vals = {
                            'name': production_code or _('Mới'),
                            'sale_order_id': sale_order.id,
                            'x_woodpro_id': production_id,
                            'date_order': self._safe_datetime(item.get('createdAt'))
                        }
                        if not prod_order:
                            prod_order = prod_order_obj.create(order_vals)
                        elif self.x_sync_mode == 'overwrite':
                            prod_order.write(order_vals)
                            self.env['dl.dossier.ledger'].search([('production_id', '=', prod_order.id)]).unlink()
                            prod_order.product_line_ids.unlink()

                        # LOGIC: GOM NHÓM THEO SẢN PHẨM VÀ BÓC TÁCH CHUYẾN
                        grouped_products = {}
                        all_trips_data = []
                        
                        for detail in item.get('productionDetails', []):
                            product_code = detail.get('product', {}).get('code')
                            if not product_code: continue
                            
                            if product_code not in grouped_products:
                                product = self.env['product.product'].search([('default_code', '=', product_code)], limit=1)
                                if not product:
                                    product = self.env['product.product'].create({
                                        'name': detail.get('product', {}).get('name'), 
                                        'default_code': product_code,
                                        'type': 'consu', 'is_storable': True, 'is_wood_product': True
                                    })
                                grouped_products[product_code] = {
                                    'product_id': product.id,
                                    'conversion_rate': self._safe_float(detail.get('conversion'), 1.3),
                                    'boms': {}
                                }
                            
                            manifests = detail.get('manifestNum', [])
                            license_plates = detail.get('licensePlate', [])
                            all_trips_data.append({
                                'product_id': grouped_products[product_code]['product_id'],
                                'manifest_num': manifests[0] if manifests else '',
                                'quantity': self._safe_float(detail.get('quantity', 0.0)),
                                'license_plate': license_plates[0] if license_plates else '',
                                'date_ship': self._safe_datetime(item.get('timeAt')),
                                'x_woodpro_id': detail.get('id')
                            })

                            for bom in detail.get('boms', []):
                                mining_id = bom.get('miningId')
                                if not mining_id: continue
                                rate = self._safe_float(bom.get('rate'))
                                norm = self._safe_float(bom.get('conversion'))
                                
                                if mining_id not in grouped_products[product_code]['boms']:
                                    species_name = bom.get('nameSci') or bom.get('subWood', {}).get('wood', {}).get('name')
                                    species = species_obj.search([('name', '=', species_name)], limit=1)
                                    if not species and species_name: species = species_obj.create({'name': species_name})
                                    grouped_products[product_code]['boms'][mining_id] = {
                                        'species_id': species.id if species else False,
                                        'rate': rate,
                                        'norm': norm
                                    }
                                else:
                                    grouped_products[product_code]['boms'][mining_id]['rate'] = rate
                                    grouped_products[product_code]['boms'][mining_id]['norm'] = norm

                        # 1. Cập nhật các chuyến vận chuyển
                        prod_order.trip_ids.unlink()
                        trip_vals = [(0, 0, t) for t in all_trips_data]
                        if trip_vals: prod_order.write({'trip_ids': trip_vals})

                        # 2. Cập nhật dòng thành phẩm & BOM
                        for p_code, p_data in grouped_products.items():
                            prod_line = prod_line_obj.search([
                                ('production_order_id', '=', prod_order.id),
                                ('product_id', '=', p_data['product_id'])
                            ], limit=1)
                            
                            line_vals = {
                                'production_order_id': prod_order.id, 
                                'product_id': p_data['product_id'],
                                'x_conversion_rate': p_data['conversion_rate']
                            }
                            if not prod_line: prod_line = prod_line_obj.create(line_vals)
                            else: prod_line.write(line_vals)
                            
                            manual_total_qty = sum([t['quantity'] for t in all_trips_data if t['product_id'] == p_data['product_id']])
                            prod_line.material_line_ids.unlink()
                            material_vals = []
                            for m_id, m_data in p_data['boms'].items():
                                dossier = self.env['dl.wood.dossier'].search([('x_woodpro_id', '=', m_id)], limit=1)
                                norm_to_use = dossier.x_default_norm if dossier else m_data['norm']
                                vol_calc = manual_total_qty * norm_to_use * (m_data['rate'] / 100.0)
                                material_vals.append((0, 0, {
                                    'species_id': m_data['species_id'], 
                                    'dossier_id': dossier.id if dossier else False,
                                    'volume_planned': vol_calc, 'volume_actual': vol_calc,
                                    'x_rate': m_data['rate'], 'x_norm': norm_to_use,
                                }))
                            if material_vals: prod_line.write({'material_line_ids': material_vals})

                        if prod_order.state != 'done' or self.x_sync_mode == 'overwrite':
                            prod_order.write({'state': 'done'})
                            prod_order._action_deduct_materials(force=True)
                        total_synced += 1
                    if page >= data.get('result', {}).get('totalPages', 1): break
                    page += 1
            return self._show_notification(_('Thành công'), _('Đã gom nhóm và đồng bộ %s đơn hàng.') % total_synced)
        except Exception as e:
            _logger.error("Lỗi đồng bộ đơn hàng: %s", str(e), exc_info=True)
            self._add_debug_log("Lỗi đồng bộ đơn hàng", str(e))
            raise UserError(_('Lỗi đồng bộ: %s') % str(e))

    def _sync_dossier_attachments(self, dossier, headers):
        if not dossier.x_woodpro_id: return
        try:
            base = self.base_url.rstrip('/')
            url = f"{base}/contracts/{dossier.x_woodpro_id}?version=tt262025" if base.endswith('/v1') else f"{base}/v1/contracts/{dossier.x_woodpro_id}?version=tt262025"
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code != 200: return
            files_data = response.json().get('result', []) if isinstance(response.json(), dict) else response.json()
            if not isinstance(files_data, list): return
            dossier.attachment_ids.unlink()
            for f in files_data:
                f_id = f.get('id')
                if not f_id: continue
                f_name = f.get('name')
                f_type = "forest_exploitation" if "Phiếu thông tin khai thác" in f_name else "hsg" if "Hợp đồng" in f_name else "manifest" if "Bảng kê lâm sản" in f_name else False
                download_url = f"{base}/views/{f_id}?type=forest_exploitation&version=tt262025&woodType=wood" if base.endswith('/v1') else f"{base}/v1/views/{f_id}?type=forest_exploitation&version=tt262025&woodType=wood"
                self.env['dl.wood.dossier.attachment'].create({
                    'dossier_id': dossier.id, 'name': f_name, 'x_woodpro_id': f_id, 'status': f.get('status'), 'url': download_url, 'file_type': f_type
                })
        except: pass

    def _show_notification(self, title, message):
        return {
            'type': 'ir.actions.client', 'tag': 'display_notification',
            'params': {'title': title, 'message': message, 'type': 'success', 'sticky': False}
        }
