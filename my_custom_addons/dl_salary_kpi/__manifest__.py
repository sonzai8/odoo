{
    'name': 'Cân Đối Lương & KPI Đức Lâm',
    'version': '19.0.1.0.0',
    'summary': 'Quản lý cân đối lương, thưởng và KPI hàng tháng',
    'description': """
        Module hỗ trợ:
        - Nhập doanh thu công ty theo tháng.
        - Nhập phụ cấp, thưởng và KPI cho nhân viên.
        - Cân đối lương và xuất file Excel theo template của xưởng gỗ Đức Lâm.
    """,
    'category': 'Human Resources/Payroll',
    'author': 'Đức Lâm Wood',
    'depends': ['hr', 'dl_wood_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'data/attendance_type_data.xml',
        'wizard/dl_salary_kpi_export_wizard_views.xml',
        'wizard/dl_salary_kpi_import_attendance_wizard_views.xml',
        'wizard/dl_salary_kpi_export_loader_views.xml',
        'views/dl_salary_kpi_attendance_type_views.xml',
        'views/dl_salary_kpi_calc_views.xml',
        'views/dl_salary_kpi_employee_views.xml',
        'views/dl_salary_kpi_month_views.xml',
        'views/dl_salary_kpi_notice_views.xml',
        'views/menus.xml',
    ],
    'assets': {},
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
