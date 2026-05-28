# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class MisaBridgeController(http.Controller):

    @http.route('/api/misa_bridge/validation_rules', type='json', auth='user', cors='*')
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

        return {
            'status': 'success',
            'data': {
                'regex': regex_list[0] if regex_list else '^sonzai',
                'errorMessage': error_list[0] if error_list else 'Mã sản phẩm không hợp lệ.',
                'rules': rules
            }
        }

    @http.route('/api/misa_bridge/peeling_types', type='json', auth='user', cors='*')
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

    @http.route('/api/misa_bridge/product/create', type='json', auth='user', cors='*')
    def create_product(self, **kwargs):
        """Nhận payload từ Extension và tạo Product trên Odoo."""
        try:
            Product = request.env['product.template'].sudo()
            
            with request.env.cr.savepoint():
                vals = {
                    'name': 'Gỗ dán (ván ép) công nghiệp phủ phim',
                    'x_is_wood_product': True,
                    'x_thickness': float(kwargs.get('thickness', 0) or 0),
                    'x_length': float(kwargs.get('length', 2440) or 2440),
                    'x_width': float(kwargs.get('width', 1220) or 1220),
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
