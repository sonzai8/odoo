# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SalaryKpiLine(models.Model):
    _name = 'dl.salary.kpi.line'
    _description = 'Dòng chấm công tháng'
    _order = 'dl_tax_department_id, dl_first_name'

    month_id = fields.Many2one('dl.salary.kpi.month', string='Tháng bảng công', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True)
    employee_name = fields.Char(related='employee_id.name', string='Tên nhân viên', store=True)
    dl_first_name = fields.Char(related='employee_id.dl_first_name', string='Tên riêng', store=True)
    identification_id = fields.Char(related='employee_id.identification_id', string='Số CCCD', store=True)
    
    dl_tax_department_id = fields.Many2one('dl.tax.department', related='employee_id.dl_tax_department_id', string='Phòng ban', store=True)
    dl_tax_id = fields.Char(related='employee_id.dl_tax_id', string='Mã số thuế', store=True)
    birthday = fields.Date(related='employee_id.birthday', string='Ngày sinh')
    sex = fields.Selection(related='employee_id.sex', string='Giới tính')
    dl_tax_position = fields.Char(related='employee_id.dl_tax_position', string='Chức vụ')
    dl_tax_base_salary = fields.Float(related='employee_id.dl_tax_base_salary', string='Lương cơ bản')


    # Chấm công 31 ngày (hiển thị mã công)
    day_01 = fields.Many2one('dl.salary.kpi.attendance.type', string='01', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_02 = fields.Many2one('dl.salary.kpi.attendance.type', string='02', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_03 = fields.Many2one('dl.salary.kpi.attendance.type', string='03', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_04 = fields.Many2one('dl.salary.kpi.attendance.type', string='04', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_05 = fields.Many2one('dl.salary.kpi.attendance.type', string='05', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_06 = fields.Many2one('dl.salary.kpi.attendance.type', string='06', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_07 = fields.Many2one('dl.salary.kpi.attendance.type', string='07', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_08 = fields.Many2one('dl.salary.kpi.attendance.type', string='08', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_09 = fields.Many2one('dl.salary.kpi.attendance.type', string='09', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_10 = fields.Many2one('dl.salary.kpi.attendance.type', string='10', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_11 = fields.Many2one('dl.salary.kpi.attendance.type', string='11', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_12 = fields.Many2one('dl.salary.kpi.attendance.type', string='12', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_13 = fields.Many2one('dl.salary.kpi.attendance.type', string='13', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_14 = fields.Many2one('dl.salary.kpi.attendance.type', string='14', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_15 = fields.Many2one('dl.salary.kpi.attendance.type', string='15', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_16 = fields.Many2one('dl.salary.kpi.attendance.type', string='16', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_17 = fields.Many2one('dl.salary.kpi.attendance.type', string='17', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_18 = fields.Many2one('dl.salary.kpi.attendance.type', string='18', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_19 = fields.Many2one('dl.salary.kpi.attendance.type', string='19', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_20 = fields.Many2one('dl.salary.kpi.attendance.type', string='20', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_21 = fields.Many2one('dl.salary.kpi.attendance.type', string='21', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_22 = fields.Many2one('dl.salary.kpi.attendance.type', string='22', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_23 = fields.Many2one('dl.salary.kpi.attendance.type', string='23', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_24 = fields.Many2one('dl.salary.kpi.attendance.type', string='24', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_25 = fields.Many2one('dl.salary.kpi.attendance.type', string='25', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_26 = fields.Many2one('dl.salary.kpi.attendance.type', string='26', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_27 = fields.Many2one('dl.salary.kpi.attendance.type', string='27', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_28 = fields.Many2one('dl.salary.kpi.attendance.type', string='28', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_29 = fields.Many2one('dl.salary.kpi.attendance.type', string='29', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_30 = fields.Many2one('dl.salary.kpi.attendance.type', string='30', domain="[('apply_to', 'in', ['normal', 'both'])]")
    day_31 = fields.Many2one('dl.salary.kpi.attendance.type', string='31', domain="[('apply_to', 'in', ['normal', 'both'])]")

    # Các trường ẩn để xác định Chủ Nhật và Tuần (dùng cho giao diện)
    day_01_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_01_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_01_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_02_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_02_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_02_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_03_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_03_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_03_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_04_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_04_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_04_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_05_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_05_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_05_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_06_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_06_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_06_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_07_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_07_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_07_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_08_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_08_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_08_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_09_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_09_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_09_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_10_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_10_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_10_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_11_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_11_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_11_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_12_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_12_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_12_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_13_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_13_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_13_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_14_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_14_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_14_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_15_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_15_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_15_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_16_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_16_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_16_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_17_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_17_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_17_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_18_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_18_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_18_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_19_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_19_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_19_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_20_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_20_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_20_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_21_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_21_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_21_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_22_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_22_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_22_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_23_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_23_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_23_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_24_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_24_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_24_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_25_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_25_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_25_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_26_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_26_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_26_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_27_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_27_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_27_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_28_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_28_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_28_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_29_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_29_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_29_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_30_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_30_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_30_row = fields.Integer(compute='_compute_day_metadata', store=True)
    day_31_is_sunday = fields.Boolean(compute='_compute_day_metadata', store=True)
    day_31_week = fields.Integer(compute='_compute_day_metadata', store=True)
    day_31_row = fields.Integer(compute='_compute_day_metadata', store=True)

    # 35 Virtual fields for 5 weeks (Mon-Sun grid)
    v01 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v01')
    v01_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v01_ot')
    v01_label = fields.Char(compute='_compute_virtual_days')
    v01_sun = fields.Boolean(compute='_compute_virtual_days')
    v02 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v02')
    v02_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v02_ot')
    v02_label = fields.Char(compute='_compute_virtual_days')
    v02_sun = fields.Boolean(compute='_compute_virtual_days')
    v03 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v03')
    v03_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v03_ot')
    v03_label = fields.Char(compute='_compute_virtual_days')
    v03_sun = fields.Boolean(compute='_compute_virtual_days')
    v04 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v04')
    v04_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v04_ot')
    v04_label = fields.Char(compute='_compute_virtual_days')
    v04_sun = fields.Boolean(compute='_compute_virtual_days')
    v05 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v05')
    v05_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v05_ot')
    v05_label = fields.Char(compute='_compute_virtual_days')
    v05_sun = fields.Boolean(compute='_compute_virtual_days')
    v06 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v06')
    v06_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v06_ot')
    v06_label = fields.Char(compute='_compute_virtual_days')
    v06_sun = fields.Boolean(compute='_compute_virtual_days')
    v07 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v07')
    v07_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v07_ot')
    v07_label = fields.Char(compute='_compute_virtual_days')
    v07_sun = fields.Boolean(compute='_compute_virtual_days')
    v08 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v08')
    v08_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v08_ot')
    v08_label = fields.Char(compute='_compute_virtual_days')
    v08_sun = fields.Boolean(compute='_compute_virtual_days')
    v09 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v09')
    v09_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v09_ot')
    v09_label = fields.Char(compute='_compute_virtual_days')
    v09_sun = fields.Boolean(compute='_compute_virtual_days')
    v10 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v10')
    v10_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v10_ot')
    v10_label = fields.Char(compute='_compute_virtual_days')
    v10_sun = fields.Boolean(compute='_compute_virtual_days')
    v11 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v11')
    v11_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v11_ot')
    v11_label = fields.Char(compute='_compute_virtual_days')
    v11_sun = fields.Boolean(compute='_compute_virtual_days')
    v12 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v12')
    v12_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v12_ot')
    v12_label = fields.Char(compute='_compute_virtual_days')
    v12_sun = fields.Boolean(compute='_compute_virtual_days')
    v13 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v13')
    v13_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v13_ot')
    v13_label = fields.Char(compute='_compute_virtual_days')
    v13_sun = fields.Boolean(compute='_compute_virtual_days')
    v14 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v14')
    v14_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v14_ot')
    v14_label = fields.Char(compute='_compute_virtual_days')
    v14_sun = fields.Boolean(compute='_compute_virtual_days')
    v15 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v15')
    v15_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v15_ot')
    v15_label = fields.Char(compute='_compute_virtual_days')
    v15_sun = fields.Boolean(compute='_compute_virtual_days')
    v16 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v16')
    v16_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v16_ot')
    v16_label = fields.Char(compute='_compute_virtual_days')
    v16_sun = fields.Boolean(compute='_compute_virtual_days')
    v17 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v17')
    v17_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v17_ot')
    v17_label = fields.Char(compute='_compute_virtual_days')
    v17_sun = fields.Boolean(compute='_compute_virtual_days')
    v18 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v18')
    v18_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v18_ot')
    v18_label = fields.Char(compute='_compute_virtual_days')
    v18_sun = fields.Boolean(compute='_compute_virtual_days')
    v19 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v19')
    v19_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v19_ot')
    v19_label = fields.Char(compute='_compute_virtual_days')
    v19_sun = fields.Boolean(compute='_compute_virtual_days')
    v20 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v20')
    v20_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v20_ot')
    v20_label = fields.Char(compute='_compute_virtual_days')
    v20_sun = fields.Boolean(compute='_compute_virtual_days')
    v21 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v21')
    v21_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v21_ot')
    v21_label = fields.Char(compute='_compute_virtual_days')
    v21_sun = fields.Boolean(compute='_compute_virtual_days')
    v22 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v22')
    v22_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v22_ot')
    v22_label = fields.Char(compute='_compute_virtual_days')
    v22_sun = fields.Boolean(compute='_compute_virtual_days')
    v23 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v23')
    v23_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v23_ot')
    v23_label = fields.Char(compute='_compute_virtual_days')
    v23_sun = fields.Boolean(compute='_compute_virtual_days')
    v24 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v24')
    v24_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v24_ot')
    v24_label = fields.Char(compute='_compute_virtual_days')
    v24_sun = fields.Boolean(compute='_compute_virtual_days')
    v25 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v25')
    v25_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v25_ot')
    v25_label = fields.Char(compute='_compute_virtual_days')
    v25_sun = fields.Boolean(compute='_compute_virtual_days')
    v26 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v26')
    v26_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v26_ot')
    v26_label = fields.Char(compute='_compute_virtual_days')
    v26_sun = fields.Boolean(compute='_compute_virtual_days')
    v27 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v27')
    v27_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v27_ot')
    v27_label = fields.Char(compute='_compute_virtual_days')
    v27_sun = fields.Boolean(compute='_compute_virtual_days')
    v28 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v28')
    v28_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v28_ot')
    v28_label = fields.Char(compute='_compute_virtual_days')
    v28_sun = fields.Boolean(compute='_compute_virtual_days')
    v29 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v29')
    v29_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v29_ot')
    v29_label = fields.Char(compute='_compute_virtual_days')
    v29_sun = fields.Boolean(compute='_compute_virtual_days')
    v30 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v30')
    v30_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v30_ot')
    v30_label = fields.Char(compute='_compute_virtual_days')
    v30_sun = fields.Boolean(compute='_compute_virtual_days')
    v31 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v31')
    v31_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v31_ot')
    v31_label = fields.Char(compute='_compute_virtual_days')
    v31_sun = fields.Boolean(compute='_compute_virtual_days')
    v32 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v32')
    v32_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v32_ot')
    v32_label = fields.Char(compute='_compute_virtual_days')
    v32_sun = fields.Boolean(compute='_compute_virtual_days')
    v33 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v33')
    v33_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v33_ot')
    v33_label = fields.Char(compute='_compute_virtual_days')
    v33_sun = fields.Boolean(compute='_compute_virtual_days')
    v34 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v34')
    v34_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v34_ot')
    v34_label = fields.Char(compute='_compute_virtual_days')
    v34_sun = fields.Boolean(compute='_compute_virtual_days')
    v35 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v35')
    v35_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v35_ot')
    v35_label = fields.Char(compute='_compute_virtual_days')
    v35_sun = fields.Boolean(compute='_compute_virtual_days')

    # Các trường liên kết để lấy mã công (dùng cho decoration trên web)
    day_01_code = fields.Char(related='day_01.code', store=True)
    day_02_code = fields.Char(related='day_02.code', store=True)
    day_03_code = fields.Char(related='day_03.code', store=True)
    day_04_code = fields.Char(related='day_04.code', store=True)
    day_05_code = fields.Char(related='day_05.code', store=True)
    day_06_code = fields.Char(related='day_06.code', store=True)
    day_07_code = fields.Char(related='day_07.code', store=True)
    day_08_code = fields.Char(related='day_08.code', store=True)
    day_09_code = fields.Char(related='day_09.code', store=True)
    day_10_code = fields.Char(related='day_10.code', store=True)
    day_11_code = fields.Char(related='day_11.code', store=True)
    day_12_code = fields.Char(related='day_12.code', store=True)
    day_13_code = fields.Char(related='day_13.code', store=True)
    day_14_code = fields.Char(related='day_14.code', store=True)
    day_15_code = fields.Char(related='day_15.code', store=True)
    day_16_code = fields.Char(related='day_16.code', store=True)
    day_17_code = fields.Char(related='day_17.code', store=True)
    day_18_code = fields.Char(related='day_18.code', store=True)
    day_19_code = fields.Char(related='day_19.code', store=True)
    day_20_code = fields.Char(related='day_20.code', store=True)
    day_21_code = fields.Char(related='day_21.code', store=True)
    day_22_code = fields.Char(related='day_22.code', store=True)
    day_23_code = fields.Char(related='day_23.code', store=True)
    day_24_code = fields.Char(related='day_24.code', store=True)
    day_25_code = fields.Char(related='day_25.code', store=True)
    day_26_code = fields.Char(related='day_26.code', store=True)
    day_27_code = fields.Char(related='day_27.code', store=True)
    day_28_code = fields.Char(related='day_28.code', store=True)
    day_29_code = fields.Char(related='day_29.code', store=True)
    day_30_code = fields.Char(related='day_30.code', store=True)
    day_31_code = fields.Char(related='day_31.code', store=True)

    # Các trường chấm công Làm thêm giờ (Overtime)
    ot_day_01 = fields.Many2one('dl.salary.kpi.attendance.type', string='01', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_02 = fields.Many2one('dl.salary.kpi.attendance.type', string='02', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_03 = fields.Many2one('dl.salary.kpi.attendance.type', string='03', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_04 = fields.Many2one('dl.salary.kpi.attendance.type', string='04', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_05 = fields.Many2one('dl.salary.kpi.attendance.type', string='05', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_06 = fields.Many2one('dl.salary.kpi.attendance.type', string='06', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_07 = fields.Many2one('dl.salary.kpi.attendance.type', string='07', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_08 = fields.Many2one('dl.salary.kpi.attendance.type', string='08', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_09 = fields.Many2one('dl.salary.kpi.attendance.type', string='09', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_10 = fields.Many2one('dl.salary.kpi.attendance.type', string='10', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_11 = fields.Many2one('dl.salary.kpi.attendance.type', string='11', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_12 = fields.Many2one('dl.salary.kpi.attendance.type', string='12', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_13 = fields.Many2one('dl.salary.kpi.attendance.type', string='13', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_14 = fields.Many2one('dl.salary.kpi.attendance.type', string='14', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_15 = fields.Many2one('dl.salary.kpi.attendance.type', string='15', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_16 = fields.Many2one('dl.salary.kpi.attendance.type', string='16', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_17 = fields.Many2one('dl.salary.kpi.attendance.type', string='17', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_18 = fields.Many2one('dl.salary.kpi.attendance.type', string='18', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_19 = fields.Many2one('dl.salary.kpi.attendance.type', string='19', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_20 = fields.Many2one('dl.salary.kpi.attendance.type', string='20', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_21 = fields.Many2one('dl.salary.kpi.attendance.type', string='21', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_22 = fields.Many2one('dl.salary.kpi.attendance.type', string='22', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_23 = fields.Many2one('dl.salary.kpi.attendance.type', string='23', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_24 = fields.Many2one('dl.salary.kpi.attendance.type', string='24', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_25 = fields.Many2one('dl.salary.kpi.attendance.type', string='25', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_26 = fields.Many2one('dl.salary.kpi.attendance.type', string='26', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_27 = fields.Many2one('dl.salary.kpi.attendance.type', string='27', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_28 = fields.Many2one('dl.salary.kpi.attendance.type', string='28', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_29 = fields.Many2one('dl.salary.kpi.attendance.type', string='29', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_30 = fields.Many2one('dl.salary.kpi.attendance.type', string='30', domain="[('apply_to', 'in', ['overtime', 'both'])]")
    ot_day_31 = fields.Many2one('dl.salary.kpi.attendance.type', string='31', domain="[('apply_to', 'in', ['overtime', 'both'])]")

    # Trường tổng hợp để phục vụ tìm kiếm/lọc
    attendance_type_ids = fields.Many2many(
        'dl.salary.kpi.attendance.type',
        compute='_compute_attendance_type_ids',
        store=True,
        string='Các loại công trong tháng'
    )

    # Các trường tổng hợp số lượng công
    total_n = fields.Float(string='Ngày', compute='_compute_totals', store=True)
    total_d = fields.Float(string='Đêm', compute='_compute_totals', store=True)
    total_p = fields.Float(string='Phép (P)', compute='_compute_totals', store=True)
    total_pl = fields.Float(string='Phép lễ (PL)', compute='_compute_totals', store=True)
    total_kp = fields.Float(string='Không phép (KP)', compute='_compute_totals', store=True)
    total_o = fields.Float(string='Nghỉ ốm (Ô)', compute='_compute_totals', store=True)
    total_dc = fields.Float(string='Đổi ca (ĐC)', compute='_compute_totals', store=True)
    total_co = fields.Float(string='Con ốm (CÔ)', compute='_compute_totals', store=True)

    # Các trường tổng hợp Làm thêm giờ
    total_ot_n = fields.Float(string='Giờ LT (Ngày)', compute='_compute_totals', store=True)
    total_ot_d = fields.Float(string='Giờ LT (Đêm)', compute='_compute_totals', store=True)
    total_ot_all = fields.Float(string='Tổng', compute='_compute_totals', store=True)

    # Các trường chi tiết Làm thêm giờ theo yêu cầu
    total_ot_n_normal = fields.Float(string='Giờ LT Ngày thường (N)', compute='_compute_totals', store=True)
    total_ot_d_normal = fields.Float(string='Giờ LT Ngày thường (Đ)', compute='_compute_totals', store=True)
    total_ot_n_sun = fields.Float(string='Giờ LT CN (Ngày)', compute='_compute_totals', store=True)
    total_ot_d_sun = fields.Float(string='Giờ LT CN (Đêm)', compute='_compute_totals', store=True)
    total_ot_n_holiday = fields.Float(string='Giờ LT Lễ (Ngày)', compute='_compute_totals', store=True)
    total_ot_d_holiday = fields.Float(string='Giờ LT Lễ (Đêm)', compute='_compute_totals', store=True)

    # Các trường Tổng hợp Công - Lương (Payroll Summary)
    payroll_n_ca_ngay = fields.Float(string='Công thường ca ngày', compute='_compute_totals', store=True)
    payroll_d_gio_ban_ngay = fields.Float(string='Giờ ca đêm tính ngày', compute='_compute_totals', store=True)
    payroll_nghi_luong = fields.Float(string='Nghỉ hưởng 100% lương', compute='_compute_totals', store=True)
    payroll_ot_n_150 = fields.Float(string='Giờ TC ngày 150%', compute='_compute_totals', store=True)
    payroll_ot_d_130 = fields.Float(string='Giờ ca đêm thường 130%', compute='_compute_totals', store=True)
    payroll_ot_d_200 = fields.Float(string='Giờ TC đêm (không ngày) 200%', compute='_compute_totals', store=True)
    payroll_ot_d_sun_300 = fields.Float(string='Giờ TC đêm CN', compute='_compute_totals', store=True)
    tax_base_salary = fields.Float(related='employee_id.dl_tax_base_salary', string='Lương CB', store=True)
    mst = fields.Char(related='employee_id.dl_tax_id', string='MST', store=True)
    cccd = fields.Char(related='employee_id.identification_id', string='CCCD', store=True)
    attendance_summary_html = fields.Html(string='Tổng hợp mã công', compute='_compute_attendance_summary')

    @api.depends('day_01', 'day_02', 'day_03', 'day_04', 'day_05', 'day_06', 'day_07', 'day_08', 'day_09', 'day_10',
                 'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20',
                 'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31',
                 'ot_day_01', 'ot_day_02', 'ot_day_03', 'ot_day_04', 'ot_day_05', 'ot_day_06', 'ot_day_07', 'ot_day_08', 'ot_day_09', 'ot_day_10',
                 'ot_day_11', 'ot_day_12', 'ot_day_13', 'ot_day_14', 'ot_day_15', 'ot_day_16', 'ot_day_17', 'ot_day_18', 'ot_day_19', 'ot_day_20',
                 'ot_day_21', 'ot_day_22', 'ot_day_23', 'ot_day_24', 'ot_day_25', 'ot_day_26', 'ot_day_27', 'ot_day_28', 'ot_day_29', 'ot_day_30', 'ot_day_31')
    def _compute_totals(self):
        for rec in self:
            n, d, p, pl, kp, o, dc, co = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            ot_n, ot_d = 0.0, 0.0
            ot_n_normal, ot_d_normal, ot_n_sun, ot_d_sun, ot_n_holiday, ot_d_holiday = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            ot_d_200 = 0.0 # TC Đêm không làm ca ngày
            for i in range(1, 32):
                # Công thường
                att = getattr(rec, f'day_{i:02d}')
                if att:
                    code = att.code
                    if code == 'N': n += 1.0
                    elif code in ['N/1', 'N/2']: n += 0.5
                    elif code == 'Đ': d += 1.0
                    elif code in ['Đ/1', 'Đ/2']: d += 0.5
                    elif code == 'P': p += 1.0
                    elif code == 'PL': pl += 1.0
                    elif code == 'KP': kp += 1.0
                    elif code == 'Ô': o += 1.0
                    elif code == 'ĐC': dc += 1.0
                    elif code == 'CÔ': co += 1.0
                
                # Làm thêm giờ
                ot_att = getattr(rec, f'ot_day_{i:02d}')
                if ot_att:
                    code = ot_att.code or ""
                    hours = ot_att.weight * 10
                    
                    if ot_att.ot_type == 'day':
                        ot_n += hours
                        if code == '0.5N': ot_n_normal += hours
                        elif code in ['CNN', 'CNN/2']: ot_n_sun += hours
                        elif code == 'LN': ot_n_holiday += hours
                    elif ot_att.ot_type == 'night':
                        ot_d += hours
                        if code == '0.5Đ': 
                            # Kiểm tra nếu không có ca ngày (day_XX is False)
                            if not att:
                                ot_d_200 += hours
                            else:
                                ot_d_normal += hours
                        elif code in ['CNĐ', 'CNĐ/2', 'CND/2']: ot_d_sun += hours
                        elif code == 'LĐ': ot_d_holiday += hours

            rec.total_n = n
            rec.total_d = d
            rec.total_p = p
            rec.total_pl = pl
            rec.total_kp = kp
            rec.total_o = o
            rec.total_dc = dc
            rec.total_co = co
            
            rec.total_ot_n = ot_n
            rec.total_ot_d = ot_d
            rec.total_ot_all = ot_n + ot_d
            
            rec.total_ot_n_normal = ot_n_normal
            rec.total_ot_d_normal = ot_d_normal
            rec.total_ot_n_sun = ot_n_sun
            rec.total_ot_d_sun = ot_d_sun
            rec.total_ot_n_holiday = ot_n_holiday
            rec.total_ot_d_holiday = ot_d_holiday
            
            # Tính toán cho Payroll Summary
            rec.payroll_n_ca_ngay = n
            rec.payroll_d_gio_ban_ngay = round(d * 8 * 0.3125, 1)
            rec.payroll_nghi_luong = pl + p
            rec.payroll_ot_n_150 = ot_n_normal
            rec.payroll_ot_d_130 = ot_d_normal
            rec.payroll_ot_d_200 = ot_d_200
            rec.payroll_ot_d_sun_300 = ot_d_sun

    @api.depends('day_01', 'day_02', 'day_03', 'day_04', 'day_05', 'day_06', 'day_07', 'day_08', 'day_09', 'day_10',
                 'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20',
                 'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31')
    def _compute_attendance_type_ids(self):
        for rec in self:
            types = []
            for i in range(1, 32):
                val = getattr(rec, f'day_{i:02d}')
                if val:
                    types.append(val.id)
            for i in range(1, 32):
                val = getattr(rec, f'ot_day_{i:02d}')
                if val:
                    types.append(val.id)
            rec.attendance_type_ids = [(6, 0, list(set(types)))]

    def _compute_attendance_summary(self):
        for rec in self:
            counts = {}
            # Đếm công thường
            for i in range(1, 32):
                att = getattr(rec, f'day_{i:02d}')
                if att:
                    counts[att.code] = counts.get(att.code, 0) + 1
            
            # Đếm công tăng ca
            ot_counts = {}
            for i in range(1, 32):
                att = getattr(rec, f'ot_day_{i:02d}')
                if att:
                    ot_counts[att.code] = ot_counts.get(att.code, 0) + 1
            
            html = "<div class='row'><div class='col-6'><strong>Công thường:</strong><ul>"
            if not counts:
                html += "<li>(Không có)</li>"
            else:
                for code, count in sorted(counts.items()):
                    html += f"<li>{code}: {count} ngày</li>"
            html += "</ul></div><div class='col-6'><strong>Tăng ca:</strong><ul>"
            if not ot_counts:
                html += "<li>(Không có)</li>"
            else:
                for code, count in sorted(ot_counts.items()):
                    html += f"<li>{code}: {count} ngày</li>"
            html += "</ul></div></div>"
            rec.attendance_summary_html = html

    @api.depends('month_id.date_month')
    def _compute_day_metadata(self):
        from calendar import monthrange
        from datetime import date
        for rec in self:
            if not rec.month_id.date_month:
                for i in range(1, 32):
                    rec[f'day_{i:02d}_is_sunday'] = False
                    rec[f'day_{i:02d}_week'] = 0
                    rec[f'day_{i:02d}_row'] = 0
                continue
                
            d_m = rec.month_id.date_month
            year, month = d_m.year, d_m.month
            last_day = monthrange(year, month)[1]
            
            # Logic tính tuần: Bắt đầu từ 1. Tăng khi gặp Thứ 2.
            current_week = 1
            for i in range(1, 32):
                field_is_sunday = f'day_{i:02d}_is_sunday'
                field_week = f'day_{i:02d}_week'
                field_row = f'day_{i:02d}_row'
                
                if i <= last_day:
                    d = date(year, month, i)
                    # Odoo/Python weekday: 0=Mon, 1=Tue... 6=Sun
                    if d.weekday() == 0 and i > 1:
                        current_week += 1
                    
                    rec[field_is_sunday] = (d.weekday() == 6)
                    rec[field_week] = current_week
                    rec[field_row] = d.weekday() + 1 # 1-7 (Mon-Sun)
                else:
                    rec[field_is_sunday] = False
                    rec[field_week] = 0
                    rec[field_row] = 0

    @api.constrains('day_01', 'day_02', 'day_03', 'day_04', 'day_05', 'day_06', 'day_07', 'day_08', 'day_09', 'day_10',
                    'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20',
                    'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31')
    def _check_shift_change(self):
        """
        Kiểm tra quy tắc đổi ca: Nếu đổi từ công N (Ngày) sang Đ (Đêm)
        thì bắt buộc phải có ít nhất 1 ngày nghỉ ĐC ở giữa.
        """
        for rec in self:
            for i in range(1, 31):
                current_day = getattr(rec, f'day_{i:02d}')
                next_day = getattr(rec, f'day_{i+1:02d}')
                
                if current_day and next_day:
                    if current_day.code == 'Đ' and next_day.code == 'N':
                        raise ValidationError(_(
                            "Nhân viên %s: Lỗi quy tắc đổi ca tại ngày %02d-%02d. "
                            "Khi chuyển từ ca Ngày (Đ) sang ca Đêm (N), bắt buộc phải có ngày Đổi ca (ĐC) ở giữa."
                        ) % (rec.employee_name, i, i+1))

    @api.constrains('day_01', 'day_02', 'day_03', 'day_04', 'day_05', 'day_06', 'day_07', 'day_08', 'day_09', 'day_10',
                    'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20',
                    'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31')
    def _check_sunday_attendance(self):
        for rec in self:
            for i in range(1, 32):
                day_field = f'day_{i:02d}'
                is_sun_field = f'day_{i:02d}_is_sunday'
                if getattr(rec, day_field) and getattr(rec, is_sun_field):
                    raise ValidationError(_("Ngày %02d là Chủ Nhật. Không được phép chấm công thường vào ngày này. Vui lòng chấm vào phần Làm thêm giờ.") % i)

    @api.constrains('day_01', 'day_02', 'day_03', 'day_04', 'day_05', 'day_06', 'day_07', 'day_08', 'day_09', 'day_10',
                    'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20',
                    'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31',
                    'ot_day_01', 'ot_day_02', 'ot_day_03', 'ot_day_04', 'ot_day_05', 'ot_day_06', 'ot_day_07', 'ot_day_08', 'ot_day_09', 'ot_day_10',
                    'ot_day_11', 'ot_day_12', 'ot_day_13', 'ot_day_14', 'ot_day_15', 'ot_day_16', 'ot_day_17', 'ot_day_18', 'ot_day_19', 'ot_day_20',
                    'ot_day_21', 'ot_day_22', 'ot_day_23', 'ot_day_24', 'ot_day_25', 'ot_day_26', 'ot_day_27', 'ot_day_28', 'ot_day_29', 'ot_day_30', 'ot_day_31')
    def _check_departure_date_attendance(self):
        """
        Ràng buộc: Nếu nhân viên đã nghỉ việc (có dl_departure_date),
        thì không được phép có bất kỳ công nào sau ngày đó.
        """
        from datetime import date
        for rec in self:
            dep_date = rec.employee_id.dl_departure_date
            if not dep_date:
                continue
            
            month_date = rec.month_id.date_month
            if not month_date:
                continue
                
            year, month = month_date.year, month_date.month
            
            vals_to_clear = {}
            for i in range(1, 32):
                try:
                    d = date(year, month, i)
                except ValueError:
                    continue
                
                if d > dep_date:
                    if getattr(rec, f'day_{i:02d}'):
                        vals_to_clear[f'day_{i:02d}'] = False
                    if getattr(rec, f'ot_{i:02d}' if hasattr(rec, f'ot_{i:02d}') else f'ot_day_{i:02d}'):
                        vals_to_clear[f'ot_day_{i:02d}'] = False
            
            if vals_to_clear:
                # Dùng sudo().write để tránh lặp constraint vô tận nếu cần, 
                # nhưng ở đây ta chỉ cần xoá dữ liệu sai.
                # Lưu ý: rec.write sẽ kích hoạt lại constraint, nên ta kiểm tra vals_to_clear trước.
                rec.sudo().write(vals_to_clear)

    def _compute_virtual_days(self):
        for rec in self:
            mapping = {} # slot_idx -> day_idx (1-31)
            for i in range(1, 32):
                w = getattr(rec, f'day_{i:02d}_week')
                r = getattr(rec, f'day_{i:02d}_row')
                if 1 <= w <= 5 and 1 <= r <= 7:
                    slot = (w - 1) * 7 + r
                    mapping[slot] = i
            
            for s in range(1, 36):
                v_f = f'v{s:02d}'
                v_ot_f = f'v{s:02d}_ot'
                v_l_f = f'v{s:02d}_label'
                v_s_f = f'v{s:02d}_sun'
                
                day_idx = mapping.get(s)
                if day_idx:
                    rec[v_f] = getattr(rec, f'day_{day_idx:02d}')
                    rec[v_ot_f] = getattr(rec, f'ot_day_{day_idx:02d}')
                    rec[v_l_f] = f'{day_idx:02d}'
                    rec[v_s_f] = getattr(rec, f'day_{day_idx:02d}_is_sunday')
                else:
                    rec[v_f] = False
                    rec[v_ot_f] = False
                    rec[v_l_f] = "X"
                    rec[v_s_f] = False

    def _inverse_v_generic(self, slot, is_ot=False):
        for rec in self:
            mapping = {}
            for i in range(1, 32):
                w = getattr(rec, f'day_{i:02d}_week')
                r = getattr(rec, f'day_{i:02d}_row')
                if 1 <= w <= 5 and 1 <= r <= 7:
                    s = (w - 1) * 7 + r
                    mapping[s] = i
            
            day_idx = mapping.get(slot)
            if day_idx:
                field_name = f"{'ot_' if is_ot else ''}day_{day_idx:02d}"
                val = getattr(rec, f"v{slot:02d}{'_ot' if is_ot else ''}")
                setattr(rec, field_name, val)

    def _inverse_v01(self): self._inverse_v_generic(1)
    def _inverse_v01_ot(self): self._inverse_v_generic(1, True)
    def _inverse_v02(self): self._inverse_v_generic(2)
    def _inverse_v02_ot(self): self._inverse_v_generic(2, True)
    def _inverse_v03(self): self._inverse_v_generic(3)
    def _inverse_v03_ot(self): self._inverse_v_generic(3, True)
    def _inverse_v04(self): self._inverse_v_generic(4)
    def _inverse_v04_ot(self): self._inverse_v_generic(4, True)
    def _inverse_v05(self): self._inverse_v_generic(5)
    def _inverse_v05_ot(self): self._inverse_v_generic(5, True)
    def _inverse_v06(self): self._inverse_v_generic(6)
    def _inverse_v06_ot(self): self._inverse_v_generic(6, True)
    def _inverse_v07(self): self._inverse_v_generic(7)
    def _inverse_v07_ot(self): self._inverse_v_generic(7, True)
    def _inverse_v08(self): self._inverse_v_generic(8)
    def _inverse_v08_ot(self): self._inverse_v_generic(8, True)
    def _inverse_v09(self): self._inverse_v_generic(9)
    def _inverse_v09_ot(self): self._inverse_v_generic(9, True)
    def _inverse_v10(self): self._inverse_v_generic(10)
    def _inverse_v10_ot(self): self._inverse_v_generic(10, True)
    def _inverse_v11(self): self._inverse_v_generic(11)
    def _inverse_v11_ot(self): self._inverse_v_generic(11, True)
    def _inverse_v12(self): self._inverse_v_generic(12)
    def _inverse_v12_ot(self): self._inverse_v_generic(12, True)
    def _inverse_v13(self): self._inverse_v_generic(13)
    def _inverse_v13_ot(self): self._inverse_v_generic(13, True)
    def _inverse_v14(self): self._inverse_v_generic(14)
    def _inverse_v14_ot(self): self._inverse_v_generic(14, True)
    def _inverse_v15(self): self._inverse_v_generic(15)
    def _inverse_v15_ot(self): self._inverse_v_generic(15, True)
    def _inverse_v16(self): self._inverse_v_generic(16)
    def _inverse_v16_ot(self): self._inverse_v_generic(16, True)
    def _inverse_v17(self): self._inverse_v_generic(17)
    def _inverse_v17_ot(self): self._inverse_v_generic(17, True)
    def _inverse_v18(self): self._inverse_v_generic(18)
    def _inverse_v18_ot(self): self._inverse_v_generic(18, True)
    def _inverse_v19(self): self._inverse_v_generic(19)
    def _inverse_v19_ot(self): self._inverse_v_generic(19, True)
    def _inverse_v20(self): self._inverse_v_generic(20)
    def _inverse_v20_ot(self): self._inverse_v_generic(20, True)
    def _inverse_v21(self): self._inverse_v_generic(21)
    def _inverse_v21_ot(self): self._inverse_v_generic(21, True)
    def _inverse_v22(self): self._inverse_v_generic(22)
    def _inverse_v22_ot(self): self._inverse_v_generic(22, True)
    def _inverse_v23(self): self._inverse_v_generic(23)
    def _inverse_v23_ot(self): self._inverse_v_generic(23, True)
    def _inverse_v24(self): self._inverse_v_generic(24)
    def _inverse_v24_ot(self): self._inverse_v_generic(24, True)
    def _inverse_v25(self): self._inverse_v_generic(25)
    def _inverse_v25_ot(self): self._inverse_v_generic(25, True)
    def _inverse_v26(self): self._inverse_v_generic(26)
    def _inverse_v26_ot(self): self._inverse_v_generic(26, True)
    def _inverse_v27(self): self._inverse_v_generic(27)
    def _inverse_v27_ot(self): self._inverse_v_generic(27, True)
    def _inverse_v28(self): self._inverse_v_generic(28)
    def _inverse_v28_ot(self): self._inverse_v_generic(28, True)
    def _inverse_v29(self): self._inverse_v_generic(29)
    def _inverse_v29_ot(self): self._inverse_v_generic(29, True)
    def _inverse_v30(self): self._inverse_v_generic(30)
    def _inverse_v30_ot(self): self._inverse_v_generic(30, True)
    def _inverse_v31(self): self._inverse_v_generic(31)
    def _inverse_v31_ot(self): self._inverse_v_generic(31, True)
    def _inverse_v32(self): self._inverse_v_generic(32)
    def _inverse_v32_ot(self): self._inverse_v_generic(32, True)
    def _inverse_v33(self): self._inverse_v_generic(33)
    def _inverse_v33_ot(self): self._inverse_v_generic(33, True)
    def _inverse_v34(self): self._inverse_v_generic(34)
    def _inverse_v34_ot(self): self._inverse_v_generic(34, True)
    def _inverse_v35(self): self._inverse_v_generic(35)
    def _inverse_v35_ot(self): self._inverse_v_generic(35, True)
