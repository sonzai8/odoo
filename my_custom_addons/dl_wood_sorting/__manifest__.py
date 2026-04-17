# -*- coding: utf-8 -*-
{
    'name': 'DL Wood Sorting (Lương Nhặt Ván)',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Quản lý đơn giá và sản lượng công đoạn Nhặt Ván',
    'description': """
        Module quản lý đơn giá nhặt ván lũy tiến:
        - Giá theo ván 1.7 ly và 2.0 ly.
        - Phân biệt giá Mới/Cũ dựa trên BHXH và loại công.
        - Tính thưởng lũy tiến trên mức 280 bó/công.
    """,
    'author': 'Antigravity',
    'depends': ['hr', 'dl_wood_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/dl_sorting_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
