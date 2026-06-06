# -*- coding: utf-8 -*-
{
    'name': 'Đức Lâm - Quản lý Ngày Nghỉ Lễ',
    'version': '19.0.1.0.0',
    'summary': 'Quản lý danh sách các ngày nghỉ lễ chung cho toàn bộ hệ thống Đức Lâm',
    'category': 'Human Resources',
    'author': 'Đức Lâm ERP',
    'depends': ['base'],
    'data': [
        'security/dl_public_holiday_security.xml',
        'security/ir.model.access.csv',
        'views/dl_public_holiday_views.xml',          # Menu cha định nghĩa ở đây
        'wizard/dl_public_holiday_wizard_views.xml',  # Tham chiếu menu cha → phải load SAU
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
