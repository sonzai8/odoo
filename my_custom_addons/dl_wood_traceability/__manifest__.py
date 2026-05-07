# -*- coding: utf-8 -*-
{
    'name': 'Đức Lâm - Truy Xuất Nguồn Gốc Gỗ',
    'version': '19.0.2.0.0',
    'summary': 'Quản lý truy xuất nguồn gốc gỗ, hồ sơ kiểm lâm và trừ lùi song song (Nội bộ và Khai báo CO)',
    'category': 'Inventory/Warehouse',
    'author': 'Đức Lâm ERP',
    'depends': ['base', 'sale', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/dl_traceability_views.xml',
        'views/res_partner_views.xml',
        'wizard/dl_customer_import_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
