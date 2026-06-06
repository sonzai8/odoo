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
    'depends': ['hr', 'dl_wood_payroll', 'hr_homeworking'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'wizard/dl_contract_generate_wizard_views.xml',
        'wizard/dl_contract_init_wizard_views.xml',
        'wizard/dl_digitize_contract_wizard_views.xml',
        'wizard/dl_scan_doc_zip_wizard_views.xml',
        'wizard/dl_bhxh_d02_wizard_views.xml',
        'wizard/dl_contract_import_wizard_views.xml',
        'views/dl_employee_scan_doc_views.xml',
        'views/res_country_state_views.xml',
        'views/res_country_ward_views.xml',
        'views/res_company_views.xml',
        'views/menus.xml',
        'views/dl_contract_type_views.xml',
        'views/dl_contract_template_views.xml',
        'views/dl_contract_views.xml',
        'views/dl_salary_history_views.xml',
        'views/hr_employee_views.xml',
    ],
    'external_dependencies': {
        'python': ['python-docx', 'pytesseract', 'pymupdf'],
        'bin': ['tesseract'],
    },
    'assets': {
        'web.assets_backend': [
            'dl_contract/static/src/css/dl_contract.css',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
