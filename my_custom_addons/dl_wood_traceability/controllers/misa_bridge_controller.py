# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import base64
from werkzeug.exceptions import Forbidden

def split_vietnamese_company_name(name):
    company_types = [
        "Công ty TNHH Một thành viên", "Công ty TNHH MTV", "Công ty TNHH Một Thành Viên",
        "CÔNG TY TNHH MỘT THÀNH VIÊN", "CÔNG TY TNHH MTV",
        "Công ty TNHH", "CÔNG TY TNHH",
        "Công ty Cổ phần", "Công ty CP", "CÔNG TY CỔ PHẦN", "CÔNG TY CP",
        "Doanh nghiệp tư nhân", "DNTN", "DOANH NGHIỆP TƯ NHÂN",
        "Hợp tác xã", "HTX", "HỢP TÁC XÃ",
        "Công ty Hợp danh", "CÔNG TY HỢP DANH"
    ]
    
    type_label = ""
    private_name = name
    
    for t in company_types:
        if name.upper().startswith(t.upper()):
            type_label = name[:len(t)].strip()
            private_name = name[len(t):].strip()
            if private_name.startswith('-') or private_name.startswith(':'):
                private_name = private_name[1:].strip()
            break
            
    return type_label, private_name

class MisaBridgeController(http.Controller):

    @http.route('/api/misa_bridge/validation_rules', type='jsonrpc', auth='user', cors='*')
    def get_validation_rules(self):
        """
        API trả về rule kiểm tra mã sản phẩm cho Chrome Extension (Odoo Bridge).
        Yêu cầu user đã login (auth='user').
        """
        IrConfigParameter = request.env['ir.config_parameter'].sudo()
        regex_param = IrConfigParameter.get_param('misa.product_code_regex', default='^sonzai')
        error_msg_param = IrConfigParameter.get_param('misa.product_code_error_msg', default='Mã sản phẩm bắt buộc phải bắt đầu bằng chữ "sonzai".')

        regex_list = [r.strip() for r in regex_param.split('\n') if r.strip()]
        error_list = [e.strip() for e in error_msg_param.split('\n') if e.strip()]

        rules = []
        for i in range(len(regex_list)):
            regex_val = regex_list[i]
            error_msg_val = error_list[i] if i < len(error_list) else "Mã sản phẩm không hợp lệ."
            rules.append({
                'regex': regex_val,
                'errorMessage': error_msg_val
            })

        IrDefault = request.env['ir.default'].sudo()
        default_length = IrDefault._get('product.template', 'x_length') or 2440.0
        default_width = IrDefault._get('product.template', 'x_width') or 1220.0
        default_name = IrConfigParameter.get_param('misa.default_product_name', default='Gỗ dán (ván ép) công nghiệp phủ phim')

        company_name = request.env.company.name
        return {
            'status': 'success',
            'data': {
                'company_name': company_name,
                'regex': regex_list[0] if regex_list else '^sonzai',
                'errorMessage': error_list[0] if error_list else 'Mã sản phẩm không hợp lệ.',
                'rules': rules,
                'defaults': {
                    'name': default_name,
                    'length': default_length,
                    'width': default_width
                }
            }
        }

    @http.route('/api/misa_bridge/peeling_types', type='jsonrpc', auth='user', cors='*')
    def get_peeling_types(self):
        """Trả về danh sách loại ván bóc (Keo, Bạch đàn...) để Extension làm checkbox."""
        try:
            types = request.env['dl.wood.peeling.type'].sudo().search([])
            return {
                'status': 'success',
                'data': [{'id': t.id, 'name': t.name, 'code': t.code} for t in types]
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/misa_bridge/product/create', type='jsonrpc', auth='user', cors='*')
    def create_product(self, **kwargs):
        """Nhận payload từ Extension và tạo Product trên Odoo."""
        try:
            Product = request.env['product.template'].sudo()
            
            with request.env.cr.savepoint():
                # Lấy tên từ payload gửi lên, nếu không có thì lấy cấu hình
                IrConfigParameter = request.env['ir.config_parameter'].sudo()
                default_name = IrConfigParameter.get_param('misa.default_product_name', default='Gỗ dán (ván ép) công nghiệp phủ phim')
                
                vals = {
                    'name': kwargs.get('name') or default_name,
                    'x_is_wood_product': True,
                    'x_thickness': float(kwargs.get('thickness', 0) or 0),
                    'x_length': float(kwargs.get('length', 0) or 0),
                    'x_width': float(kwargs.get('width', 0) or 0),
                    'x_unit': kwargs.get('unit', 'sheet'),
                    'list_price': float(kwargs.get('price', 0) or 0),
                    'x_quality': kwargs.get('quality', ''),
                }
                
                peeling_ids = kwargs.get('peeling_type_ids', [])
                if peeling_ids:
                    vals['x_required_peeling_type_ids'] = [(6, 0, peeling_ids)]
                    
                product = Product.create(vals)
                
                # Gọi hàm sinh mã tự động
                if hasattr(product, '_onchange_wood_name_and_code'):
                    product._onchange_wood_name_and_code()
                elif hasattr(product, '_onchange_wood_name_and_code_traceability'):
                    product._onchange_wood_name_and_code_traceability()
                    
            return {
                'status': 'success',
                'data': {
                    'product_id': product.id,
                    'name': product.name,
                    'default_code': product.default_code
                }
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/misa_bridge/customer/sync', type='jsonrpc', auth='user', cors='*')
    def sync_customers(self, **kwargs):
        """Nhận danh sách khách hàng từ Extension và tạo/cập nhật trên Odoo."""
        try:
            customers = kwargs.get('customers', [])
            if not customers:
                return {'status': 'error', 'message': 'Không có dữ liệu khách hàng gửi lên.'}
                
            Partner = request.env['res.partner'].sudo()
            results = {'created': 0, 'updated': 0, 'failed': 0, 'skipped': 0, 'errors': []}
            
            # Sử dụng công ty của phiên đăng nhập hiện tại
            current_company_id = request.env.company.id
            
            for cust in customers:
                try:
                    code = cust.get('account_object_code')
                    name = cust.get('account_object_name')
                    tax_code = cust.get('company_tax_code')
                    address = cust.get('address') or cust.get('contact_address') or ''
                    misa_id = cust.get('account_object_id')
                    
                    if not code or not name:
                        results['failed'] += 1
                        results['errors'].append({
                            'code': code or '[Rỗng]',
                            'error': 'Thiếu mã (account_object_code) hoặc tên (account_object_name)'
                        })
                        continue
                        
                    # Tách tên doanh nghiệp và tên riêng
                    type_label, private_name = split_vietnamese_company_name(name)

                    # Tìm đối tác để đối chiếu
                    partner = False
                    
                    # 1. Tìm theo x_misa_id
                    if misa_id:
                        partner = Partner.search([('x_misa_id', '=', misa_id)], limit=1)
                        
                    # 2. Tìm theo ref (Mã khách hàng)
                    if not partner:
                        partner = Partner.search([('ref', '=', code)], limit=1)
                        
                    # Gộp thông tin số điện thoại di động và bàn thông minh
                    phone_misa = (cust.get('tel') or cust.get('phone') or '').strip()
                    mobile_misa = (cust.get('mobile') or '').strip()
                    
                    final_phone = False
                    if phone_misa and mobile_misa:
                        if phone_misa != mobile_misa:
                            final_phone = f"{phone_misa} / {mobile_misa}"
                        else:
                            final_phone = phone_misa
                    else:
                        final_phone = phone_misa or mobile_misa or False

                    vals = {
                        'name': name,
                        'ref': code,
                        'x_customer_code': code,
                        'vat': tax_code or False,
                        'x_misa_id': misa_id or False,
                        'x_is_wood_customer': True, # Khách hàng mua gỗ
                        'company_id': current_company_id,
                        'is_company': True,
                        'x_company_type_label': type_label or False,
                        'x_private_name': private_name or name,
                        'phone': final_phone,
                        'mobile': mobile_misa or False,
                        'email': cust.get('email') or False,
                        'website': cust.get('website') or False,
                        'x_misa_group_code': cust.get('account_object_group_code') or cust.get('account_object_group_name') or False,
                        'x_misa_contact_name': cust.get('contact_name') or False,
                    }
                    
                    # Khớp nối ngân hàng thông minh
                    bank_name = cust.get('bank_name')
                    bank_account = cust.get('bank_account') or cust.get('bank_account_number')
                    if bank_name:
                        Bank = request.env['dl.vietnam.bank'].sudo()
                        bank_rec = Bank.search([
                            '|', '|',
                            ('name', '=ilike', bank_name.strip()),
                            ('short_name', '=ilike', bank_name.strip()),
                            ('code', '=ilike', bank_name.strip())
                        ], limit=1)
                        if not bank_rec:
                            bank_rec = Bank.search([
                                '|',
                                ('name', 'ilike', bank_name.strip()),
                                ('short_name', 'ilike', bank_name.strip())
                            ], limit=1)
                        if bank_rec:
                            vals['x_bank_name_id'] = bank_rec.id
                            vals['x_bank_name'] = bank_rec.short_name
                        else:
                            vals['x_bank_name'] = bank_name
                    if bank_account:
                        vals['x_bank_account_number'] = bank_account
                        vals['x_bank_account_holder'] = name
                    
                    # Phân tách và chuẩn hóa địa chỉ Việt Nam dùng vietnamadminunits của Odoo (Cập nhật lại 100% địa chỉ)
                    if address:
                        addr_parsed = Partner.action_parse_cccd_address(address)
                        state_id = addr_parsed.get('state_id')
                        if state_id:
                            # Bóc tách thành công -> tìm và gán quốc gia Việt Nam (VN)
                            vn_country = request.env['res.country'].sudo().search([('code', '=', 'VN')], limit=1)
                            vals.update({
                                'street': addr_parsed.get('street') or address,
                                'city': addr_parsed.get('city') or False,
                                'state_id': state_id,
                                'ward_id': addr_parsed.get('ward_id') or False,
                                'country_id': vn_country.id if vn_country else False,
                                'x_misa_raw_address': address
                            })
                        else:
                            # Không bóc tách được -> chỉ lưu text thô vào street, các trường khác và quốc gia set False
                            vals.update({
                                'street': address,
                                'city': False,
                                'state_id': False,
                                'ward_id': False,
                                'country_id': False,
                                'x_misa_raw_address': address
                            })
                    else:
                        vals.update({
                            'street': False,
                            'city': False,
                            'state_id': False,
                            'ward_id': False,
                            'country_id': False,
                            'x_misa_raw_address': False
                        })
                    
                    # Phòng hờ trường hợp model không có các trường phụ
                    if 'x_misa_id' not in Partner._fields:
                        vals.pop('x_misa_id', None)
                    if 'x_customer_code' not in Partner._fields:
                        vals.pop('x_customer_code', None)
                    if 'x_is_wood_customer' not in Partner._fields:
                        vals.pop('x_is_wood_customer', None)
                    if 'x_company_type_label' not in Partner._fields:
                        vals.pop('x_company_type_label', None)
                    if 'x_private_name' not in Partner._fields:
                        vals.pop('x_private_name', None)
                    if 'x_misa_group_code' not in Partner._fields:
                        vals.pop('x_misa_group_code', None)
                    if 'x_misa_contact_name' not in Partner._fields:
                        vals.pop('x_misa_contact_name', None)
                    if 'x_misa_raw_address' not in Partner._fields:
                        vals.pop('x_misa_raw_address', None)
                    if 'mobile' not in Partner._fields:
                        vals.pop('mobile', None)
                        
                    if partner:
                        # Kiểm tra xem đối tác này có đại diện cho công ty nào trong Odoo không
                        is_represent = request.env['res.company'].sudo().search([('partner_id', '=', partner.id)], limit=1)
                        if is_represent:
                            # Bỏ qua hoàn toàn đối tác đại diện cho công ty trong Odoo
                            results['skipped'] += 1
                            results['errors'].append({
                                'code': code,
                                'error': f'Bỏ qua {name}'
                            })
                            continue

                        # Không cập nhật lại company_id cho đối tác đã tồn tại để tránh lỗi Multi-Company
                        vals.pop('company_id', None)
                        partner.write(vals)
                        results['updated'] += 1
                    else:
                        Partner.create(vals)
                        results['created'] += 1
                        
                except Exception as ex:
                    results['failed'] += 1
                    results['errors'].append({
                        'code': cust.get('account_object_code', '[Không rõ]'),
                        'error': str(ex)
                    })
                    
            return {
                'status': 'success',
                'data': results
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/misa_bridge/order/check_duplicate', type='jsonrpc', auth='user', cors='*')
    def check_duplicate_order(self, **kwargs):
        """Kiểm tra hóa đơn MISA đã được đồng bộ chưa"""
        refid = kwargs.get('refid')
        if not refid:
            return {'status': 'error', 'message': 'Thiếu refid hóa đơn MISA'}
        existing = request.env['dl.wood.sale.order'].sudo().search([('x_misa_refid', '=', refid)], limit=1)
        if existing:
            return {
                'status': 'duplicate',
                'message': f'Hóa đơn này đã được đồng bộ vào đơn đặt hàng: {existing.name}',
                'order_id': existing.id,
                'order_name': existing.name
            }
        return {'status': 'ok'}

    @http.route('/api/misa_bridge/order/sync_customer', type='jsonrpc', auth='user', cors='*')
    def sync_order_customer(self, **kwargs):
        """Đồng bộ 1 khách hàng và trả về ID"""
        customer = kwargs.get('customer')
        if not customer:
            return {'status': 'error', 'message': 'Không có dữ liệu khách hàng.'}
            
        code = customer.get('account_object_code')
        if not code:
            return {'status': 'error', 'message': 'Khách hàng không có mã (account_object_code).'}
            
        # Tái sử dụng logic đồng bộ khách hàng hiện tại
        res = self.sync_customers(customers=[customer])
        if res.get('status') != 'success':
            return res
            
        # Tìm lại đối tác đã được tạo/cập nhật
        Partner = request.env['res.partner'].sudo()
        partner = Partner.search([('ref', '=', code)], limit=1)
        
        if partner:
            return {
                'status': 'success',
                'data': {
                    'partner_id': partner.id,
                    'name': partner.name
                }
            }
        return {'status': 'error', 'message': f'Lỗi không tìm thấy khách hàng sau khi đồng bộ mã: {code}'}

    @http.route('/api/misa_bridge/order/sync_product', type='jsonrpc', auth='user', cors='*')
    def sync_order_product(self, **kwargs):
        import re
        """Đồng bộ danh sách sản phẩm và trả về map mã -> ID"""
        products = kwargs.get('products', [])
        Product = request.env['product.template'].sudo()
        ProductProduct = request.env['product.product'].sudo()
        
        results = {}
        for p in products:
            code = p.get('inventory_item_code')
            name = p.get('inventory_item_name') or p.get('description') or code
            price = float(p.get('unit_price', 0.0) or 0.0)
            if not code:
                continue
                
            prod_tmpl = Product.search([('default_code', '=', code)], limit=1)
            if not prod_tmpl:
                # Phân tích kích thước từ tên (VD: ... 15mm x 1250mm x 2500mm ...)
                thickness, width, length = 0.0, 1220.0, 2440.0
                if name:
                    match = re.search(r'(\d+(?:\.\d+)?)\s*mm\s*[xX]\s*(\d+(?:\.\d+)?)\s*mm\s*[xX]\s*(\d+(?:\.\d+)?)\s*mm', name)
                    if match:
                        thickness = float(match.group(1))
                        width = float(match.group(2))
                        length = float(match.group(3))
                
                # Nếu không tìm thấy thickness trong tên, parse thử từ mã (VD: TPEPK_T15.0...)
                if thickness <= 0 and code:
                    match_code = re.search(r'_T(\d+(?:\.\d+)?)', code)
                    if match_code:
                        thickness = float(match_code.group(1))
                
                # Đảm bảo thickness > 0 để thoả mãn Odoo constrains
                if thickness <= 0:
                    thickness = 1.0

                # Nếu chưa có thì tạo mới sản phẩm cơ bản
                prod_tmpl = Product.with_context(misa_sync=True).create({
                    'name': name or code,
                    'default_code': code,
                    'x_is_wood_product': True,
                    'type': 'consu',
                    'x_thickness': thickness,
                    'x_width': width,
                    'x_length': length,
                    'list_price': price,
                    'x_is_misa_synced': True
                })
            else:
                # Nếu đã có, cập nhật lại tên và giá từ MISA (vì MISA là master)
                prod_tmpl.with_context(misa_sync=True).write({
                    'name': name or code,
                    'list_price': price,
                    'x_is_misa_synced': True
                })
                
            # Lấy bản ghi variant product.product tương ứng
            prod = ProductProduct.search([('product_tmpl_id', '=', prod_tmpl.id)], limit=1)
            if prod:
                results[code] = prod.id
                
        return {'status': 'success', 'data': results}

    @http.route('/api/misa_bridge/order/create', type='jsonrpc', auth='user', cors='*')
    def create_misa_order(self, **kwargs):
        """Tạo đơn đặt hàng (dl.wood.sale.order) và các lệnh sản xuất"""
        try:
            partner_id = kwargs.get('partner_id')
            refid = kwargs.get('refid')
            refno = kwargs.get('refno_finance')
            date_order = kwargs.get('date') # yyyy-mm-dd
            details = kwargs.get('details', [])
            note = kwargs.get('note', '')
            
            if not partner_id or not details:
                return {'status': 'error', 'message': 'Thiếu partner_id hoặc details'}
                
            SaleOrder = request.env['dl.wood.sale.order'].sudo()
            ProductionOrder = request.env['dl.wood.production.order'].sudo()
            
            with request.env.cr.savepoint():
                # Format lại date_order nếu cần, hoặc dùng hàm mặc định nếu rỗng
                order_vals = {
                    'partner_id': partner_id,
                    'x_misa_refid': refid,
                    'x_misa_refno_finance': refno,
                    'note': f'Đồng bộ từ Hóa đơn MISA: {refno}\n{note}'.strip()
                }
                if date_order:
                    order_vals['date_order'] = date_order
                    
                order = SaleOrder.create(order_vals)
                
                for line in details:
                    product_id = line.get('product_id')
                    if not product_id:
                        continue
                        
                    qty = float(line.get('quantity', 1.0) or 1.0)
                    price = float(line.get('unit_price', 0.0) or 0.0)
                    display_name = line.get('inventory_item_name')
                    
                    ProductionOrder.create({
                        'sale_order_id': order.id,
                        'product_id': product_id,
                        'x_invoice_display_name': display_name,
                        'x_selling_price': price,
                        'qty_planned': qty,
                        'qty_done': qty,
                        'date_planned': order.date_order,
                    })
                    
            return {
                'status': 'success', 
                'data': {
                    'order_id': order.id,
                    'order_name': order.name
                }
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/misa_bridge/extension_info', type='jsonrpc', auth='user', cors='*')
    def get_extension_info(self, **kwargs):
        """Lấy thông tin phiên bản và token tải extension mới nhất"""
        try:
            company = request.env.company
            if not company.x_misa_ext_token:
                import uuid
                company.sudo().x_misa_ext_token = uuid.uuid4().hex
                
            release = request.env['dl.misa.extension.release'].sudo().search([('is_active', '=', True)], limit=1)
            return {
                'status': 'success',
                'data': {
                    'latest_version': release.name if release else '1.0',
                    'token': company.x_misa_ext_token or ''
                }
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/misa_bridge/download_extension', type='http', auth='public', cors='*', methods=['GET'])
    def download_extension(self, token=None, **kwargs):
        """API tải bộ cài Extension (File ZIP) với auth=public, bảo vệ bằng token"""
        if not token:
            raise Forbidden("Missing secure token.")
            
        company = request.env['res.company'].sudo().search([('x_misa_ext_token', '=', token)], limit=1)
        if not company:
            raise Forbidden("Invalid token.")
            
        release = request.env['dl.misa.extension.release'].sudo().search([('is_active', '=', True)], limit=1)
        if not release or not release.zip_file:
            raise Forbidden("No active extension release found.")
            
        file_content = base64.b64decode(release.zip_file)
        filename = release.filename or f'OdooBridgeExtension_v{release.name}.zip'
        
        return request.make_response(
            file_content,
            [
                ('Content-Type', 'application/zip'),
                ('Content-Disposition', f'attachment; filename="{filename}"'),
                ('Content-Length', str(len(file_content)))
            ]
        )
