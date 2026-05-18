# -*- coding: utf-8 -*-
import sys
import os
import requests

sys.path.append('/Users/sonzai/dev/odoo 19/odoo')
import odoo
from odoo import api, tools

tools.config.parse_config(['-c', 'odoo.conf'])

def inspect_wp_products():
    registry = odoo.modules.registry.Registry('odoo_db')
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        # Lấy bản ghi cấu hình WoodPro hoạt động đầu tiên
        config = env['dl.woodpro.config'].search([], limit=1)
        if not config:
            print("Không tìm thấy cấu hình WoodPro nào trong DB!")
            return
            
        print(f"Cấu hình: {config.name} - URL: {config.base_url}")
        
        # Đảm bảo đăng nhập
        if not config.token:
            config.action_login()
            print("Đã đăng nhập và lấy Token mới.")
            
        headers = {
            'Content-Type': 'application/json',
            'Cookie': f'id={config.token}',
            'User-Agent': 'Odoo/19.0'
        }
        
        url = f"{config.base_url}/products"
        params = {'page': 1, 'limit': 2}
        if config.x_woodpro_company_id:
            params['companyId'] = config.x_woodpro_company_id.wp_id
            
        print(f"Calling: {url} with params: {params}")
        response = requests.get(url, headers=headers, params=params, timeout=20)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            if not items and data.get('result'):
                res_data = data.get('result', {})
                items = res_data.get('items', []) if isinstance(res_data, dict) else []
                
            print(f"Tìm thấy {len(items)} sản phẩm.")
            for i, item in enumerate(items):
                print(f"\n--- Sản phẩm {i+1} ---")
                for key, val in item.items():
                    print(f"  {key}: {val}")
        else:
            print(f"Lỗi phản hồi: {response.text}")

if __name__ == '__main__':
    inspect_wp_products()
