# -*- coding: utf-8 -*-
{
    'name': 'DL Wood Product Base',
    'version': '19.0.1.0.0',
    'summary': 'Module lõi quản lý thông số và danh mục Sản phẩm Gỗ (Kích thước, Đặc tính, Tự động sinh mã)',
    'category': 'Inventory/Warehouse',
    'author': 'Đức Lâm ERP',
    'depends': ['base', 'product', 'sale'],
    'data': [
        'views/product_template_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dl_wood_product_base/static/src/css/style.css',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
