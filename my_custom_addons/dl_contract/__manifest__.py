# -*- coding: utf-8 -*-
{
    'name': 'DL Contract Management',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Quản lý hợp đồng lao động cho Đức Lâm',
    'description': """
        Module mở rộng để quản lý hợp đồng lao động, lịch sử lương,
        và tự động tạo file hợp đồng từ template Word (.docx).
        Hỗ trợ đa công ty (Multi-Company).
    """,
    'author': 'Antigravity',
    'depends': ['hr', 'dl_wood_payroll'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'wizard/dl_contract_generate_wizard_views.xml',
        'wizard/dl_contract_init_wizard_views.xml',
        'views/menus.xml',
        'views/dl_contract_type_views.xml',
        'views/dl_contract_template_views.xml',
        'views/dl_contract_views.xml',
        'views/dl_salary_history_views.xml',
        'views/hr_employee_views.xml',
    ],
    'external_dependencies': {
        'python': ['python-docx'],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
