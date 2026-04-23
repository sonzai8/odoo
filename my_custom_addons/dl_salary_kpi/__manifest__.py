# -*- coding: utf-8 -*-
{
    'name': 'Cân Đối Lương & KPI Đức Lâm',
    'version': '19.0.1.0.0',
    'summary': 'Quản lý loại công, lương và KPI - Xưởng gỗ Đức Lâm',
    'category': 'Human Resources/Payroll',
    'author': 'Đức Lâm Wood',
    'depends': ['base','hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/attendance_type_data.xml',
        'data/dl_tax_department_data.xml',
        'views/attendance_type_views.xml',
        'views/dl_tax_department_views.xml',
        'views/hr_employee_views.xml',
        'wizard/dl_salary_kpi_import_views.xml',
        'wizard/dl_salary_kpi_tax_import_views.xml',
        'views/dl_salary_kpi_month_views.xml',
        'views/hr_employee_tax_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dl_salary_kpi/static/src/css/matrix.css',
            'dl_salary_kpi/static/src/css/full_width_matrix.css',
        ],
    },
    'installable': True,

    'application': True,
    'license': 'LGPL-3',
}
