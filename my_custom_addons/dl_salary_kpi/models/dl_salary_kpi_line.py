# -*- coding: utf-8 -*-
import math
import random
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SalaryKpiLine(models.Model):
    _name = 'dl.salary.kpi.line'
    _description = 'Dòng chấm công tháng'
    _order = 'dl_tax_department_id, dl_first_name'

    month_id = fields.Many2one('dl.salary.kpi.month', string='Tháng bảng công', ondelete='cascade')
    month_state = fields.Selection(related='month_id.state', string='Trạng thái tháng', store=True)
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
    day_01_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_01_week = fields.Integer(compute='_compute_day_metadata')
    day_01_row = fields.Integer(compute='_compute_day_metadata')
    day_02_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_02_week = fields.Integer(compute='_compute_day_metadata')
    day_02_row = fields.Integer(compute='_compute_day_metadata')
    day_03_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_03_week = fields.Integer(compute='_compute_day_metadata')
    day_03_row = fields.Integer(compute='_compute_day_metadata')
    day_04_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_04_week = fields.Integer(compute='_compute_day_metadata')
    day_04_row = fields.Integer(compute='_compute_day_metadata')
    day_05_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_05_week = fields.Integer(compute='_compute_day_metadata')
    day_05_row = fields.Integer(compute='_compute_day_metadata')
    day_06_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_06_week = fields.Integer(compute='_compute_day_metadata')
    day_06_row = fields.Integer(compute='_compute_day_metadata')
    day_07_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_07_week = fields.Integer(compute='_compute_day_metadata')
    day_07_row = fields.Integer(compute='_compute_day_metadata')
    day_08_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_08_week = fields.Integer(compute='_compute_day_metadata')
    day_08_row = fields.Integer(compute='_compute_day_metadata')
    day_09_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_09_week = fields.Integer(compute='_compute_day_metadata')
    day_09_row = fields.Integer(compute='_compute_day_metadata')
    day_10_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_10_week = fields.Integer(compute='_compute_day_metadata')
    day_10_row = fields.Integer(compute='_compute_day_metadata')
    day_11_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_11_week = fields.Integer(compute='_compute_day_metadata')
    day_11_row = fields.Integer(compute='_compute_day_metadata')
    day_12_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_12_week = fields.Integer(compute='_compute_day_metadata')
    day_12_row = fields.Integer(compute='_compute_day_metadata')
    day_13_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_13_week = fields.Integer(compute='_compute_day_metadata')
    day_13_row = fields.Integer(compute='_compute_day_metadata')
    day_14_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_14_week = fields.Integer(compute='_compute_day_metadata')
    day_14_row = fields.Integer(compute='_compute_day_metadata')
    day_15_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_15_week = fields.Integer(compute='_compute_day_metadata')
    day_15_row = fields.Integer(compute='_compute_day_metadata')
    day_16_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_16_week = fields.Integer(compute='_compute_day_metadata')
    day_16_row = fields.Integer(compute='_compute_day_metadata')
    day_17_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_17_week = fields.Integer(compute='_compute_day_metadata')
    day_17_row = fields.Integer(compute='_compute_day_metadata')
    day_18_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_18_week = fields.Integer(compute='_compute_day_metadata')
    day_18_row = fields.Integer(compute='_compute_day_metadata')
    day_19_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_19_week = fields.Integer(compute='_compute_day_metadata')
    day_19_row = fields.Integer(compute='_compute_day_metadata')
    day_20_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_20_week = fields.Integer(compute='_compute_day_metadata')
    day_20_row = fields.Integer(compute='_compute_day_metadata')
    day_21_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_21_week = fields.Integer(compute='_compute_day_metadata')
    day_21_row = fields.Integer(compute='_compute_day_metadata')
    day_22_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_22_week = fields.Integer(compute='_compute_day_metadata')
    day_22_row = fields.Integer(compute='_compute_day_metadata')
    day_23_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_23_week = fields.Integer(compute='_compute_day_metadata')
    day_23_row = fields.Integer(compute='_compute_day_metadata')
    day_24_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_24_week = fields.Integer(compute='_compute_day_metadata')
    day_24_row = fields.Integer(compute='_compute_day_metadata')
    day_25_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_25_week = fields.Integer(compute='_compute_day_metadata')
    day_25_row = fields.Integer(compute='_compute_day_metadata')
    day_26_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_26_week = fields.Integer(compute='_compute_day_metadata')
    day_26_row = fields.Integer(compute='_compute_day_metadata')
    day_27_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_27_week = fields.Integer(compute='_compute_day_metadata')
    day_27_row = fields.Integer(compute='_compute_day_metadata')
    day_28_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_28_week = fields.Integer(compute='_compute_day_metadata')
    day_28_row = fields.Integer(compute='_compute_day_metadata')
    day_29_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_29_week = fields.Integer(compute='_compute_day_metadata')
    day_29_row = fields.Integer(compute='_compute_day_metadata')
    day_30_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_30_week = fields.Integer(compute='_compute_day_metadata')
    day_30_row = fields.Integer(compute='_compute_day_metadata')
    day_31_is_sunday = fields.Boolean(compute='_compute_day_metadata')
    day_31_week = fields.Integer(compute='_compute_day_metadata')
    day_31_row = fields.Integer(compute='_compute_day_metadata')

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
    v36 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v36')
    v36_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v36_ot')
    v36_label = fields.Char(compute='_compute_virtual_days')
    v36_sun = fields.Boolean(compute='_compute_virtual_days')
    v37 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v37')
    v37_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v37_ot')
    v37_label = fields.Char(compute='_compute_virtual_days')
    v37_sun = fields.Boolean(compute='_compute_virtual_days')
    v38 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v38')
    v38_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v38_ot')
    v38_label = fields.Char(compute='_compute_virtual_days')
    v38_sun = fields.Boolean(compute='_compute_virtual_days')
    v39 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v39')
    v39_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v39_ot')
    v39_label = fields.Char(compute='_compute_virtual_days')
    v39_sun = fields.Boolean(compute='_compute_virtual_days')
    v40 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v40')
    v40_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v40_ot')
    v40_label = fields.Char(compute='_compute_virtual_days')
    v40_sun = fields.Boolean(compute='_compute_virtual_days')
    v41 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v41')
    v41_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v41_ot')
    v41_label = fields.Char(compute='_compute_virtual_days')
    v41_sun = fields.Boolean(compute='_compute_virtual_days')
    v42 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v42')
    v42_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v42_ot')
    v42_label = fields.Char(compute='_compute_virtual_days')
    v42_sun = fields.Boolean(compute='_compute_virtual_days')

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
    bonus_p_day = fields.Float(string='Thưởng chuyên cần', compute='_compute_totals', store=True, help="Nếu làm trên 20 công (Ngày + Đêm) sẽ được tặng 1 công phép.")
    total_attendance_month = fields.Float(string='Tổng công trong tháng', compute='_compute_totals', store=True, help="Tổng công ngày + đêm + công phép thưởng")
    
    payroll_n_ca_ngay = fields.Float(string='Công thường ca ngày', compute='_compute_totals', store=True)
    payroll_d_gio_ban_ngay = fields.Float(string='Giờ ca đêm tính ngày', compute='_compute_totals', store=True)
    payroll_ot_n_150 = fields.Float(string='Giờ TC ngày 150%', compute='_compute_totals', store=True)
    payroll_ot_d_130 = fields.Float(string='Giờ ca đêm thường 130%', compute='_compute_totals', store=True)
    payroll_ot_d_200 = fields.Float(string='Giờ TC đêm (không ngày) 200%', compute='_compute_totals', store=True)
    payroll_ot_d_sun_300 = fields.Float(string='Giờ TC đêm CN', compute='_compute_totals', store=True)
    tax_base_salary = fields.Float(related='employee_id.dl_tax_base_salary', string='Lương CB', store=True)
    mst = fields.Char(related='employee_id.dl_tax_id', string='MST', store=True)
    cccd = fields.Char(related='employee_id.identification_id', string='CCCD', store=True)
    
    # --- CÁC KHOẢN THU NHẬP NỘI BỘ ---
    payroll_meal_allowance = fields.Monetary(string='Hỗ trợ ăn ca', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_women_allowance = fields.Monetary(string='Phụ cấp phụ nữ', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    
    # Chia nhỏ các loại thưởng năm
    payroll_bonus_0803 = fields.Monetary(string='Thưởng 08/03', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_bonus_3004 = fields.Monetary(string='Thưởng 30/04', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_bonus_0209 = fields.Monetary(string='Thưởng 02/09', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_bonus_tet_dl = fields.Monetary(string='Thưởng Tết DL', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_bonus_other = fields.Monetary(string='Thưởng khác', compute='_compute_payroll_internal', store=True, currency_field='currency_id')

    payroll_annual_bonus = fields.Monetary(string='Tổng thưởng năm', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_revenue_bonus = fields.Monetary(string='Thưởng doanh thu', compute='_compute_payroll_internal', store=True, currency_field='currency_id', help="Thưởng doanh thu thực tế = (Mức thưởng theo doanh thu tháng * Số ngày làm thực tế) / 26")
    payroll_productivity_bonus = fields.Monetary(string='Thưởng Năng Suất', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_total_rev_prod_bonus = fields.Monetary(string='Tổng thưởng DT & Năng Suất', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_total_bonus = fields.Monetary(string='Tổng trợ cấp & thưởng năm', compute='_compute_payroll_internal', store=True, currency_field='currency_id', help="Tổng các khoản trợ cấp & thưởng năm = Ăn ca + Phụ cấp phụ nữ + Tổng thưởng năm (lễ/tết)")
    
    # --- CÁC KHOẢN THEO CHẾ ĐỘ (LÝ THUYẾT 26 NGÀY) ---
    payroll_regime_meal_allowance = fields.Monetary(string='Hỗ trợ ăn ca (Chế độ)', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_regime_women_allowance = fields.Monetary(string='Phụ cấp phụ nữ (Chế độ)', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_regime_revenue_bonus = fields.Monetary(string='Thưởng doanh thu (Chế độ)', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_regime_productivity_bonus = fields.Monetary(string='Thưởng Năng Suất (Chế độ)', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_regime_total_rev_prod_bonus = fields.Monetary(string='Tổng thưởng DT & Năng Suất (Chế độ)', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_total_regime_income = fields.Monetary(string='Tổng thu nhập chế độ', compute='_compute_payroll_internal', store=True, currency_field='currency_id', help="Lương cơ bản + Phụ cấp phụ nữ + Hỗ trợ ăn ca + Thưởng doanh thu/Năng suất (mức 26 ngày)")

    # --- CÁC KHOẢN LƯƠNG CHI TIẾT ---
    payroll_wage_day = fields.Monetary(string='Lương ca ngày', compute='_compute_payroll_internal', store=True, currency_field='currency_id', help="Lương ca ngày = (Số công ca ngày thường N + Số ngày nghỉ hưởng lương P, PL) * Đơn giá lương giờ")
    payroll_wage_day_150 = fields.Monetary(string='Lương TC ngày 150%', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_wage_night_130 = fields.Monetary(string='Lương ca đêm thường 130%', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_wage_night_200 = fields.Monetary(string='Lương TC đêm 200% (Ko ngày)', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_wage_night_210 = fields.Monetary(string='Lương TC đêm 210% (Có ngày)', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_wage_night_sun_270 = fields.Monetary(string='Lương TC đêm CN 270%', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_wage_day_sun_200 = fields.Monetary(string='Lương CN ca ngày 200%', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_wage_day_holiday_300 = fields.Monetary(string='Lương Lễ ca ngày 300%', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_wage_night_holiday_390 = fields.Monetary(string='Lương TC đêm Lễ 390%', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    
    payroll_total_wage = fields.Monetary(string='Tổng lương', compute='_compute_payroll_internal', store=True, currency_field='currency_id', help="Tổng lương = Tổng các khoản lương chi tiết (ngày, đêm, tăng ca...) + Thưởng doanh thu thực tế")
    payroll_total_actual_income = fields.Monetary(string='Tổng thu nhập thực tế', compute='_compute_payroll_internal', store=True, currency_field='currency_id', help="Tổng thu nhập thực tế = Tổng lương + Các khoản trợ cấp thực tế (đã tỷ lệ theo công)")

    # --- CÁC KHOẢN KHẤU TRỪ ---
    payroll_deduction_bhxh = fields.Monetary(string='BHXH (8%)', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_deduction_bhyt = fields.Monetary(string='BHYT (1.5%)', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_deduction_bhtn = fields.Monetary(string='BHTN (1%)', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_deduction_tncn = fields.Monetary(string='Thuế TNCN', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_total_insurance_deduction = fields.Monetary(string='Tổng cộng trừ bảo hiểm', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    
    # --- CÁC TRƯỜNG PHỤC VỤ THUẾ TNCN ---
    payroll_pit_taxable_income = fields.Monetary(string='Thu nhập chịu thuế (TNCT)', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_pit_number_of_dependents = fields.Integer(string='Số người phụ thuộc', compute='_compute_payroll_internal', store=True)
    payroll_pit_total_deductions = fields.Monetary(string='Tổng các khoản giảm trừ', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_pit_assessable_income = fields.Monetary(string='Thu nhập tính thuế (TNTT)', compute='_compute_payroll_internal', store=True, currency_field='currency_id')

    payroll_total_deduction = fields.Monetary(string='Tổng các khoản trừ', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_net_salary_base = fields.Monetary(string='Thực lĩnh ngoài (Lk)', compute='_compute_payroll_internal', store=True, currency_field='currency_id', aggregator='sum')
    payroll_net_salary = fields.Monetary(string='Thực lĩnh cuối cùng', compute='_compute_payroll_internal', store=True, currency_field='currency_id', aggregator='sum')

    # --- TỰ ĐỘNG SINH ĐIỂM KPI ---
    payroll_internal_salary = fields.Monetary(string='Lương trong (Ln)', currency_field='currency_id', aggregator='sum', help="Lương thực tế muốn trả cho nhân viên (Target Salary)")
    payroll_kpi_score = fields.Float(string='Điểm KPI (Sinh ra)', digits=(16, 2), aggregator="avg")
    payroll_kpi_amount = fields.Monetary(string='Tiền KPI (Cân đối)', currency_field='currency_id', aggregator='sum')
    payroll_cash_amount = fields.Monetary(string='Tiền mặt trả thêm', currency_field='currency_id', aggregator='sum')
    
    payroll_bank_transfer_amount = fields.Monetary(string='Tiền chuyển khoản', compute='_compute_payroll_internal', store=True, currency_field='currency_id', aggregator='sum')
    payroll_bank_transfer_amount_rounded = fields.Monetary(string='Tiền CK làm tròn', compute='_compute_payroll_internal', store=True, currency_field='currency_id', aggregator='sum')
    payroll_bank_transfer_amount_rounding_error = fields.Monetary(string='Sai số CK', compute='_compute_payroll_internal', store=True, currency_field='currency_id', aggregator='sum')
    payroll_cash_amount_rounded = fields.Monetary(string='Tiền mặt làm tròn', compute='_compute_payroll_internal', store=True, currency_field='currency_id', aggregator='sum')
    payroll_cash_amount_rounding_error = fields.Monetary(string='Sai số Tiền mặt', compute='_compute_payroll_internal', store=True, currency_field='currency_id', aggregator='sum')
    total_normal_weekday_days = fields.Integer(string='Tổng công thường T2-T7', compute='_compute_payroll_internal', store=True)

    payroll_anomaly_suggestion = fields.Html(string='Gợi ý xử lý', compute='_compute_payroll_internal', store=True)
    payroll_income_explanation = fields.Html(string='Diễn giải thu nhập', compute='_compute_payroll_internal', store=True)

    @api.depends('payroll_net_salary_base', 'payroll_kpi_amount', 'payroll_cash_amount')
    def _compute_final_rounding(self):
        for rec in self:
            bank_transfer = (rec.payroll_net_salary_base or 0) + (rec.payroll_kpi_amount or 0)
            rec.payroll_bank_transfer_amount = bank_transfer
            
            # Làm tròn xuống hàng nghìn cho Tiền chuyển khoản
            rounded_bt = (bank_transfer // 1000) * 1000 if bank_transfer else 0
            rec.payroll_bank_transfer_amount_rounded = rounded_bt
            rec.payroll_bank_transfer_amount_rounding_error = bank_transfer - rounded_bt
            
            # Làm tròn xuống hàng nghìn cho Tiền mặt
            cash = rec.payroll_cash_amount or 0
            rounded_cash = (cash // 1000) * 1000 if cash else 0
            rec.payroll_cash_amount_rounded = rounded_cash
            rec.payroll_cash_amount_rounding_error = cash - rounded_cash

    # --- CHI TIẾT TIÊU CHÍ KPI ---
    kpi_c1_productivity = fields.Float(string='Năng suất/Chất lượng (Max 40)', digits=(16, 2))
    kpi_c2_discipline = fields.Float(string='Kỷ luật/An toàn (Max 30)', digits=(16, 2))
    kpi_c3_teamwork = fields.Float(string='Làm việc nhóm (Max 15)', digits=(16, 2))
    kpi_c4_5s = fields.Float(string='Vệ sinh/5S (Max 10)', digits=(16, 2))
    kpi_c5_saving = fields.Float(string='Tiết kiệm (Max 5)', digits=(16, 2))

    currency_id = fields.Many2one('res.currency', related='month_id.currency_id', string='Tiền tệ')

    attendance_summary_html = fields.Html(string='Tổng hợp mã công', compute='_compute_attendance_summary')

    def action_reset_data(self):
        """Xoá sạch toàn bộ dữ liệu tính toán, chỉ để lại mã chấm công thô."""
        vals = {
            # Tổng hợp công thường
            'total_n': 0, 'total_d': 0, 'total_p': 0, 'total_pl': 0,
            'total_kp': 0, 'total_o': 0, 'total_dc': 0, 'total_co': 0,
            # Tổng hợp tăng ca
            'total_ot_n': 0, 'total_ot_d': 0, 'total_ot_all': 0,
            'total_ot_n_normal': 0, 'total_ot_d_normal': 0, 'total_ot_n_sun': 0, 
            'total_ot_d_sun': 0, 'total_ot_n_holiday': 0, 'total_ot_d_holiday': 0,
            # Payroll Summary
            'payroll_n_ca_ngay': 0, 'payroll_d_gio_ban_ngay': 0,
            'bonus_p_day': 0, 'total_attendance_month': 0,
            'payroll_ot_n_150': 0, 'payroll_ot_d_130': 0, 'payroll_ot_d_200': 0, 'payroll_ot_d_sun_300': 0,
            # Thu nhập & Phụ cấp
            'payroll_meal_allowance': 0, 'payroll_women_allowance': 0,
            'payroll_bonus_0803': 0, 'payroll_bonus_3004': 0, 'payroll_bonus_0209': 0, 
            'payroll_bonus_tet_dl': 0, 'payroll_bonus_other': 0,
            'payroll_annual_bonus': 0, 'payroll_revenue_bonus': 0, 'payroll_productivity_bonus': 0,
            'payroll_total_bonus': 0, 'payroll_total_regime_income': 0,
            # Lương chi tiết
            'payroll_wage_day': 0, 'payroll_wage_day_150': 0, 'payroll_wage_night_130': 0,
            'payroll_wage_night_200': 0, 'payroll_wage_night_210': 0, 'payroll_wage_night_sun_270': 0,
            'payroll_wage_day_sun_200': 0, 'payroll_wage_day_holiday_300': 0, 'payroll_wage_night_holiday_390': 0,
            'payroll_total_wage': 0,
            # KPI
            'payroll_kpi_score': 0, 'payroll_kpi_amount': 0, 'payroll_cash_amount': 0,
        }
        self.write(vals)

    @api.depends('day_01', 'day_02', 'day_03', 'day_04', 'day_05', 'day_06', 'day_07', 'day_08', 'day_09', 'day_10',
                 'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20',
                 'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31',
                 'ot_day_01', 'ot_day_02', 'ot_day_03', 'ot_day_04', 'ot_day_05', 'ot_day_06', 'ot_day_07', 'ot_day_08', 'ot_day_09', 'ot_day_10',
                 'ot_day_11', 'ot_day_12', 'ot_day_13', 'ot_day_14', 'ot_day_15', 'ot_day_16', 'ot_day_17', 'ot_day_18', 'ot_day_19', 'ot_day_20',
                 'ot_day_21', 'ot_day_22', 'ot_day_23', 'ot_day_24', 'ot_day_25', 'ot_day_26', 'ot_day_27', 'ot_day_28', 'ot_day_29', 'ot_day_30', 'ot_day_31')
    def action_generate_kpi_scores(self, max_allowed=70):
        """
        Thuật toán Tự động sinh Điểm KPI dựa trên Lương nội bộ (Ln).
        - Đảm bảo điểm KPI chẵn.
        - Tiền mặt >= 1 triệu hoặc = 0 (trừ trường hợp ngoại lệ).
        - Tổng thực nhận luôn khớp tuyệt đối Ln.
        """
        from odoo.exceptions import UserError
        import math
        
        for rec in self:
            if rec.month_id.state in ['lock_kpi', 'confirmed']:
                raise UserError("Bảng lương đã chốt KPI hoặc đã xác nhận, không thể tính toán lại.")
            
            ln = rec.payroll_internal_salary
            lk = rec.payroll_net_salary_base
            
            if not ln or lk <= 0:
                rec.write({'payroll_kpi_score': 0, 'payroll_kpi_amount': 0, 'payroll_cash_amount': 0})
                continue
            
            gap = ln - lk
            max_mk = lk * (max_allowed - 50) / 50.0
            
            if gap <= 0:
                p_final = 50.0
                mk = 0.0
                cash = 0.0
            elif gap <= max_mk:
                # Đủ sức dùng 100% KPI (Không dùng Tiền mặt)
                # Cho phép điểm KPI lẻ để khớp hoàn toàn Ln = Lk + Mk
                p_final = 50.0 + 50.0 * gap / lk
                mk = gap
                cash = 0.0
            else:
                # Bắt buộc dùng Tiền mặt
                cash_needed = gap - max_mk
                if cash_needed >= 1000000:
                    # Tiền mặt đủ lớn, lấy ngẫu nhiên Điểm KPI trước
                    if random.random() < 0.7:
                        p_temp = random.uniform(60.0, float(max_allowed))
                    else:
                        p_temp = random.uniform(50.0, float(max_allowed))
                    
                    mk_temp = lk * (p_temp - 50.0) / 50.0
                    cash_raw = gap - mk_temp
                    # Làm tròn Tiền mặt đến hàng chục nghìn (10.000 VNĐ)
                    cash = round(cash_raw / 10000.0) * 10000
                    # Tính ngược lại Điểm KPI lẻ để khớp hoàn toàn
                    mk = gap - cash
                    p_final = 50.0 + 50.0 * mk / lk
                else:
                    # Tiền mặt < 1 triệu, tính p_theo để nhường chỗ 1 triệu cho Tiền mặt
                    remaining_gap = gap - 1000000
                    if remaining_gap < 0:
                        # Edge case: Tổng khoảng cách < 1 triệu
                        p_final = 50.0
                        mk = 0.0
                        cash = gap
                    else:
                        # Normal case: Lấy p_upper là điểm tối đa để vẫn còn 1tr Tiền mặt
                        p_upper = 50.0 + 50.0 * remaining_gap / lk
                        if p_upper >= 60 and random.random() < 0.7:
                            p_temp = random.uniform(60.0, float(min(max_allowed, p_upper)))
                        else:
                            p_temp = random.uniform(50.0, float(min(max_allowed, p_upper)))
                        
                        mk_temp = lk * (p_temp - 50.0) / 50.0
                        cash_raw = gap - mk_temp
                        # Làm tròn Tiền mặt đến hàng chục nghìn
                        cash = round(cash_raw / 10000.0) * 10000
                        mk = gap - cash
                        p_final = 50.0 + 50.0 * mk / lk
                
                # --- KIỂM SOÁT BIÊN (CAPPING) ---
                # Nếu sau khi làm tròn mà p_final vượt ngưỡng cho phép
                if p_final > max_allowed:
                    p_final = float(max_allowed)
                    mk = lk * (p_final - 50.0) / 50.0
                    cash = gap - mk
                
            # Đảm bảo p_final luôn làm tròn 2 chữ số thập phân cho đẹp
            p_final = round(p_final, 2)
            mk = gap - cash # Đảm bảo mk + cash luôn bằng gap
            
            # --- PHÂN RÃ ĐIỂM KPI THÀNH 5 TIÊU CHÍ (C1-C5) TỶ LỆ THUẬN ---
            # Giới hạn: C1: 40, C2: 30, C3: 15, C4: 10, C5: 5 (Tổng max = 100)
            limits = [40, 30, 15, 10, 5]
            target_ratio = p_final / 100.0
            kpi_vals = [0.0] * 5
            
            # 1. Tính toán giá trị nguyên cho C2, C3, C4, C5 (Tỷ lệ thuận + Ngẫu nhiên)
            for i in range(1, 5):
                variance = random.uniform(0.9, 1.1)
                # Sử dụng int(round(...)) để ép về số nguyên tuyệt đối
                val = int(round(limits[i] * target_ratio * variance))
                # Đảm bảo tối thiểu 1 điểm nếu p_final đủ lớn, và không vượt quá giới hạn
                min_val = 1 if p_final > 30 else 0
                kpi_vals[i] = float(max(min_val, min(limits[i], val)))
            
            # 2. Tiêu chí 1 (C1) gánh toàn bộ phần lẻ để khớp p_final
            # C1 = p_final - (tổng các số nguyên C2, C3, C4, C5)
            kpi_vals[0] = round(p_final - sum(kpi_vals[1:5]), 2)
            
            # 3. Xử lý trường hợp C1 vượt ngưỡng (Cap at 40)
            if kpi_vals[0] > limits[0]:
                excess = kpi_vals[0] - limits[0]
                kpi_vals[0] = float(limits[0])
                # Phân bổ phần dư vào các tiêu chí khác (vẫn giữ nguyên số nguyên)
                for i in range(1, 5):
                    if excess <= 0: break
                    can_add = limits[i] - kpi_vals[i]
                    if can_add > 0:
                        add = min(math.ceil(excess), can_add)
                        kpi_vals[i] += add
                        excess -= add
                # Nếu vẫn còn dư sau khi đã kịch trần tất cả (hy hữu), cộng nốt vào C1 
                # (Dù sẽ vượt 40 một chút nhưng đảm bảo khớp Ln)
                if excess > 0:
                    kpi_vals[0] = round(kpi_vals[0] + excess, 2)
            
            rec.write({
                'payroll_kpi_score': p_final,
                'payroll_kpi_amount': mk,
                'payroll_cash_amount': cash,
                'kpi_c1_productivity': kpi_vals[0],
                'kpi_c2_discipline': kpi_vals[1],
                'kpi_c3_teamwork': kpi_vals[2],
                'kpi_c4_5s': kpi_vals[3],
                'kpi_c5_saving': kpi_vals[4],
            })

    @api.depends('day_01', 'day_02', 'day_03', 'day_04', 'day_05', 'day_06', 'day_07', 'day_08', 'day_09', 'day_10',
                 'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20',
                 'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31',
                 'ot_day_01', 'ot_day_02', 'ot_day_03', 'ot_day_04', 'ot_day_05', 'ot_day_06', 'ot_day_07', 'ot_day_08', 'ot_day_09', 'ot_day_10',
                 'ot_day_11', 'ot_day_12', 'ot_day_13', 'ot_day_14', 'ot_day_15', 'ot_day_16', 'ot_day_17', 'ot_day_18', 'ot_day_19', 'ot_day_20',
                 'ot_day_21', 'ot_day_22', 'ot_day_23', 'ot_day_24', 'ot_day_25', 'ot_day_26', 'ot_day_27', 'ot_day_28', 'ot_day_29', 'ot_day_30', 'ot_day_31')
    def _compute_totals(self):
        from . import attendance_logic
        if not self:
            return
            
        # Tải trước toàn bộ mã công vào RAM để tránh N+1 Query
        att_types = self.env['dl.salary.kpi.attendance.type'].search([])
        att_map = {t.id: {'code': t.code, 'weight': t.weight, 'ot_type': t.ot_type} for t in att_types}
        
        for rec in self:
            res = attendance_logic.calculate_attendance_totals(rec, att_map=att_map)
            
            # Gán kết quả vào các trường tổng hợp (đẩy 1 lần vào cache bằng update)
            rec.update({
                'total_n': res['total_n'],
                'total_d': res['total_d'],
                'total_p': res['total_p'],
                'total_pl': res['total_pl'],
                'total_kp': res['total_kp'],
                'total_o': res['total_o'],
                'total_dc': res['total_dc'],
                'total_co': res['total_co'],
                'total_ot_n': res['ot_n'],
                'total_ot_d': res['ot_d'],
                'total_ot_all': res['ot_all'],
                'total_ot_n_normal': res['ot_n_normal'],
                'total_ot_d_normal': res['ot_d_normal'],
                'total_ot_n_sun': res['ot_n_sun'],
                'total_ot_d_sun': res['ot_d_sun'],
                'total_ot_n_holiday': res['ot_n_holiday'],
                'total_ot_d_holiday': res['ot_d_holiday'],
                
                # Tính toán cho Payroll Summary
                'bonus_p_day': res['bonus_p_day'],
                'total_attendance_month': res['total_n'] + res['total_d'] + res['bonus_p_day'],
                'payroll_n_ca_ngay': res['total_n'],
                'payroll_d_gio_ban_ngay': round(res['total_d'] * 8 * 0.3125, 1),
                'payroll_ot_n_150': res['ot_n_normal'],
                'payroll_ot_d_130': round(res['total_d'] * 8 * 0.6875, 1),
                'payroll_ot_d_200': res['ot_d_normal'],
                'payroll_ot_d_sun_300': res['ot_d_sun']
            })

    @api.depends('month_id.dl_revenue', 'month_id.dl_production_volume', 'month_id.dl_meal_allowance', 
                 'month_id.dl_women_allowance', 'month_id.bonus_line_ids', 'employee_id.sex', 
                 'dl_tax_base_salary', 'dl_tax_position', 'payroll_n_ca_ngay', 'total_n', 'total_d',
                 'total_ot_n_normal', 'total_ot_d_normal', 'total_ot_n_sun', 'total_ot_d_sun', 
                 'total_ot_n_holiday', 'total_ot_d_holiday', 'day_01', 'day_02', 'day_03', 'day_04', 'day_05', 
                 'day_06', 'day_07', 'day_08', 'day_09', 'day_10', 'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 
                 'day_16', 'day_17', 'day_18', 'day_19', 'day_20', 'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 
                 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31',
                 'ot_day_01', 'ot_day_02', 'ot_day_03', 'ot_day_04', 'ot_day_05', 'ot_day_06', 'ot_day_07', 'ot_day_08', 'ot_day_09', 'ot_day_10',
                 'ot_day_11', 'ot_day_12', 'ot_day_13', 'ot_day_14', 'ot_day_15', 'ot_day_16', 'ot_day_17', 'ot_day_18', 'ot_day_19', 'ot_day_20',
                 'ot_day_21', 'ot_day_22', 'ot_day_23', 'ot_day_24', 'ot_day_25', 'ot_day_26', 'ot_day_27', 'ot_day_28', 'ot_day_29', 'ot_day_30', 'ot_day_31',
                 'payroll_kpi_amount', 'payroll_cash_amount')
    def _compute_payroll_internal(self):
        from . import payroll_logic
        if not self:
            return
            
        # Tải trước (Prefetch) toàn bộ nhân viên và dữ liệu cấu hình tháng bằng 1 query
        self.mapped('employee_id.dependent_ids')
        self.mapped('month_id')
        
        import datetime
        for rec in self:
            year = rec.month_id.date_month.year if rec.month_id.date_month else datetime.date.today().year
            month = rec.month_id.date_month.month if rec.month_id.date_month else datetime.date.today().month
            normal_weekdays = 0
            for day in range(1, 32):
                field_name = f'day_{day:02d}'
                day_val = getattr(rec, field_name, False)
                if day_val and getattr(day_val, 'code', '') in ('N', 'Đ'):
                    try:
                        d = datetime.date(year, month, day)
                        if d.weekday() < 6: # 0-5 is Mon-Sat
                            normal_weekdays += 1
                    except ValueError:
                        pass
            
            # 1. Hỗ trợ & Phụ cấp
            meal_allowance, women_allowance = payroll_logic.calculate_allowances(rec)
            
            # 2. Thưởng cố định năm
            b0803, b3004, b0209, btet, bother = payroll_logic.calculate_annual_bonuses(rec)
            annual_bonus = b0803 + b3004 + b0209 + btet + bother
            
            # 3. Thưởng doanh thu & Năng suất (Theo chính sách QĐ 3108)
            revenue_bonus, productivity_bonus, rev_bonus_base, prod_bonus_base = payroll_logic.calculate_revenue_productivity_bonuses(rec)
            
            # Tổng trợ cấp & thưởng năm = Ăn ca + Phụ cấp phụ nữ + Thưởng năm
            total_bonus = meal_allowance + women_allowance + annual_bonus
            
            # --- TÍNH TOÁN LƯƠNG CHẾ ĐỘ (THEO LÝ THUYẾT 26 CÔNG) ---
            meal_allowance_regime = rec.month_id.dl_meal_allowance or 0.0
            is_female = rec.employee_id.sex == 'female'
            women_allowance_regime = rec.month_id.dl_women_allowance if is_female else 0.0
            
            # Tổng thu nhập chế độ = Lương cơ bản lý thuyết + Phụ cấp phụ nữ + Ăn ca + Thưởng doanh thu lý thuyết + Thưởng NS lý thuyết
            total_regime_income = (
                rec.dl_tax_base_salary + 
                women_allowance_regime + 
                meal_allowance_regime + 
                rev_bonus_base +
                prod_bonus_base
            )

            # 4. Tính toán lương chi tiết
            wages = payroll_logic.calculate_detailed_wages(rec)
            
            # Tổng lương chi tiết (Chỉ bao gồm lương công, không bao gồm thưởng)
            total_detailed_wage = sum(wages.values())
            
            # Tổng thu nhập thực tế = Lương chi tiết + Thưởng (DT + NS) + Trợ cấp thực tế + Tiền KPI
            total_actual_income = (
                total_detailed_wage + 
                revenue_bonus + 
                productivity_bonus + 
                meal_allowance + 
                women_allowance + 
                max(0, rec.payroll_kpi_amount)
            )

            # 5. Khấu trừ & Thực lĩnh
            # Thuế và bảo hiểm tính trên Thu nhập cơ bản (không bao gồm KPI/Cash cân đối)
            # Thu nhập chịu thuế (không bao gồm KPI/Cash cân đối)
            base_income = total_detailed_wage + revenue_bonus + productivity_bonus + meal_allowance + women_allowance
            deductions = payroll_logic.calculate_deductions(rec, base_income, meal_allowance)
            
            # Thực lĩnh cơ sở (Lk) = Thu nhập cơ bản - Khấu trừ
            net_salary_base = base_income - deductions['total_deduction']
            
            # Thực lĩnh cuối cùng = Thực lĩnh cơ sở + KPI + Cash (không được trừ tiền mặt)
            net_salary_final = net_salary_base + max(0, rec.payroll_kpi_amount) + max(0, rec.payroll_cash_amount)
            
            # 6. Gợi ý xử lý dữ liệu bất thường
            anomaly_suggestion = ""
            buffer = 300000 # 1 ngày công
            if rec.payroll_internal_salary > 0:
                diff = net_salary_base - rec.payroll_internal_salary
                h_rate = rec.dl_tax_base_salary / 208.0 if rec.dl_tax_base_salary else 0
                ins_factor = 0.895 # Ước tính sau khi trừ 10.5% BH
                
                if h_rate > 0:
                    import math
                    # Giá trị Net ước tính cho từng loại công
                    v_05n = 4.0 * 1.5 * h_rate * ins_factor
                    v_05d = 4.0 * 2.0 * h_rate * ins_factor
                    
                    meal_day = (rec.month_id.dl_meal_allowance or 0.0) / 26.0
                    women_day = (rec.month_id.dl_women_allowance or 0.0) / 26.0 if rec.employee_id.sex == 'female' else 0.0
                    
                    # Giá trị N gộp = Lương N (8h) + Ăn ca + Phụ nữ + Lương 0.5N đi kèm
                    v_n_full = (8.0 * h_rate * ins_factor) + meal_day + women_day + v_05n
                    # Giá trị Đ gộp = Lương Đ quy đổi (8h) + Ăn ca + Phụ nữ + Lương 0.5Đ đi kèm
                    v_d_full = ((8.0 * 0.3125 * h_rate) + (8.0 * 0.6875 * h_rate * 1.3)) * ins_factor + meal_day + women_day + v_05d
                    
                    if diff > -buffer:
                        # Thực lĩnh ngoài (Lk) quá cao, cần GIẢM công
                        c_05n = math.ceil(max(0, diff) / v_05n) if v_05n > 0 else 0
                        c_05d = math.ceil(max(0, diff) / v_05d) if v_05d > 0 else 0
                        c_n = math.ceil(max(0, diff) / v_n_full) if v_n_full > 0 else 0
                        c_d = math.ceil(max(0, diff) / v_d_full) if v_d_full > 0 else 0
                        
                        if diff > 0:
                            header = f"<div style='color: #d9534f; font-weight: bold;'>🔻 Thực lĩnh ngoài VƯỢT Thực lĩnh nội bộ. Cần giảm ít nhất:</div>"
                        else:
                            header = f"<div style='color: #f0ad4e; font-weight: bold;'>⚠️ Thực lĩnh ngoài sát Thực lĩnh nội bộ. Nên giảm bớt:</div>"

                        anomaly_suggestion = (
                            header +
                            f"<ul style='margin-bottom: 0; padding-left: 20px; color: #333;'>"
                            f"<li>Giảm <b>{max(1, c_05n)}</b> lần <b>0.5N</b></li>"
                            f"<li>Hoặc <b>{max(1, c_05d)}</b> lần <b>0.5Đ</b></li>"
                            f"<li>Hoặc <b>{max(1, c_n)}</b> ngày <b>N</b></li>"
                            f"</ul>"
                        )
                    elif rec.payroll_internal_salary >= (net_salary_base * 1.4):
                        # Thực lĩnh nội bộ (Ln) quá cao, chênh lệch lớn, cần THÊM công
                        gap = -diff
                        c_05n = math.ceil(gap / v_05n) if v_05n > 0 else 0
                        c_05d = math.ceil(gap / v_05d) if v_05d > 0 else 0
                        c_n = math.ceil(gap / v_n_full) if v_n_full > 0 else 0
                        
                        header = f"<div style='color: #5cb85c; font-weight: bold;'>🟢 Chênh lệch quá lớn. Có thể thêm tối đa:</div>"
                        anomaly_suggestion = (
                            header +
                            f"<ul style='margin-bottom: 0; padding-left: 20px; color: #333;'>"
                            f"<li>Thêm <b>{max(1, c_05n)}</b> lần <b>0.5N</b></li>"
                            f"<li>Hoặc <b>{max(1, c_05d)}</b> lần <b>0.5Đ</b></li>"
                            f"<li>Hoặc <b>{max(1, c_n)}</b> ngày <b>N</b></li>"
                            f"</ul>"
                        )

            # Đẩy tất cả dữ liệu vào cache một lần bằng update
            rec.update({
                'total_normal_weekday_days': normal_weekdays,
                'payroll_anomaly_suggestion': anomaly_suggestion,
                'payroll_meal_allowance': meal_allowance,
                'payroll_women_allowance': women_allowance,
                'payroll_regime_meal_allowance': meal_allowance_regime,
                'payroll_regime_women_allowance': women_allowance_regime,
                'payroll_regime_revenue_bonus': rev_bonus_base,
                'payroll_regime_productivity_bonus': prod_bonus_base,
                'payroll_regime_total_rev_prod_bonus': rev_bonus_base + prod_bonus_base,
                'payroll_bonus_0803': b0803,
                'payroll_bonus_3004': b3004,
                'payroll_bonus_0209': b0209,
                'payroll_bonus_tet_dl': btet,
                'payroll_bonus_other': bother,
                'payroll_annual_bonus': annual_bonus,
                'payroll_revenue_bonus': revenue_bonus,
                'payroll_productivity_bonus': productivity_bonus,
                'payroll_total_rev_prod_bonus': revenue_bonus + productivity_bonus,
                'payroll_total_bonus': total_bonus,
                'payroll_total_regime_income': total_regime_income,
                'payroll_wage_day': wages['wage_day'],
                'payroll_wage_day_150': wages['wage_day_150'],
                'payroll_wage_night_130': wages['wage_night_130'],
                'payroll_wage_night_200': wages['wage_night_200'],
                'payroll_wage_night_210': wages['wage_night_210'],
                'payroll_wage_night_sun_270': wages['wage_night_sun_270'],
                'payroll_wage_day_sun_200': wages['wage_day_sun_200'],
                'payroll_wage_day_holiday_300': wages['wage_day_holiday_300'],
                'payroll_wage_night_holiday_390': wages['wage_night_holiday_390'],
                'payroll_total_wage': total_detailed_wage + revenue_bonus + productivity_bonus,
                'payroll_total_actual_income': total_actual_income,
                'payroll_income_explanation': self._get_income_explanation(
                    total_detailed_wage, revenue_bonus, productivity_bonus, 
                    meal_allowance, women_allowance, rec.payroll_kpi_amount
                ),
                
                # Cập nhật các khoản trừ & Thuế TNCN
                'payroll_deduction_bhxh': deductions['bhxh'],
                'payroll_deduction_bhyt': deductions['bhyt'],
                'payroll_deduction_bhtn': deductions['bhtn'],
                'payroll_deduction_tncn': deductions['tncn'],
                'payroll_total_insurance_deduction': deductions['total_insurance'],
                'payroll_pit_taxable_income': deductions['taxable_income'],
                'payroll_pit_number_of_dependents': deductions['num_dependents'],
                'payroll_pit_total_deductions': deductions['total_pit_deductions'],
                'payroll_pit_assessable_income': deductions['assessable_income'],
                'payroll_total_deduction': deductions['total_deduction'],
                'payroll_net_salary_base': net_salary_base,
                'payroll_net_salary': net_salary_final,
            })
                
            # Cập nhật các trường Tiền chuyển khoản và làm tròn
            # Sử dụng round() để tránh sai số dấu phẩy động (9199999.999... // 1000 = 9199)
            transfer_val = net_salary_base + (rec.payroll_kpi_amount or 0)
            transfer_val_clean = round(transfer_val)
            rounded_transfer = (transfer_val_clean // 1000) * 1000 if transfer_val_clean else 0
            
            cash_val = rec.payroll_cash_amount or 0
            cash_val_clean = round(cash_val)
            rounded_cash = (cash_val_clean // 1000) * 1000 if cash_val_clean else 0

            rec.update({
                'payroll_bank_transfer_amount': transfer_val,
                'payroll_bank_transfer_amount_rounded': rounded_transfer,
                'payroll_bank_transfer_amount_rounding_error': transfer_val - rounded_transfer,
                'payroll_cash_amount_rounded': rounded_cash,
                'payroll_cash_amount_rounding_error': cash_val - rounded_cash,
            })

    def _get_income_explanation(self, wage, rev, prod, meal, women, kpi):
        """Hàm hỗ trợ tạo chuỗi diễn giải chi tiết bằng HTML"""
        parts = []
        def fmt(val):
            return "{:,.0f}".format(val or 0).replace(",", ".")
            
        if wage: parts.append(f"<b>{fmt(wage)}</b> (Lương CT)")
        if rev: parts.append(f"<b>{fmt(rev)}</b> (Thưởng DT)")
        if prod: parts.append(f"<b>{fmt(prod)}</b> (Thưởng NS)")
        if meal: parts.append(f"<b>{fmt(meal)}</b> (Ăn ca)")
        if women: parts.append(f"<b>{fmt(women)}</b> (Phụ nữ)")
        if kpi: parts.append(f"<b>{fmt(kpi)}</b> (KPI)")
        
        if not parts: return ""
        
        formula = " + ".join(parts)
        total = (wage or 0) + (rev or 0) + (prod or 0) + (meal or 0) + (women or 0) + (kpi or 0)
        return f"<div style='text-align: right; color: #444; font-size: 0.95em; border-top: 1px dashed #ccc; padding-top: 5px; margin-top: 5px;'>{formula} = <span style='color: #d9534f; font-weight: bold;'>{fmt(total)}</span></div>"

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
        from . import attendance_logic
        for rec in self:
            rec.attendance_summary_html = attendance_logic.get_attendance_summary_html(rec)

    @api.depends('month_id.date_month')
    def _compute_day_metadata_old(self):
        """
        Bản gốc chưa tối ưu (giữ lại để tham chiếu / dự phòng).
        Vấn đề: 330 nhân viên * 31 ngày * 3 trường = 30.690 lệnh gán ORM -> chậm ~27s.
        """
        from . import attendance_logic
        for rec in self:
            metadata = attendance_logic.get_day_metadata(rec.month_id.date_month)
            for i in range(1, 32):
                data = metadata.get(i, {'is_sunday': False, 'week': 0, 'row': 0})
                rec[f'day_{i:02d}_is_sunday'] = data['is_sunday']
                rec[f'day_{i:02d}_week'] = data['week']
                rec[f'day_{i:02d}_row'] = data['row']

    @api.depends('month_id.date_month')
    def _compute_day_metadata(self):
        """
        Phiên bản tối ưu hoá (Batch update cache).
        Tất cả nhân viên trong cùng 1 tháng có metadata giống nhau tuyệt đối.
        Nên ta tính toán metadata một lần, gom thành 1 cục data `vals`,
        rồi dùng update() đẩy thẳng 93 giá trị vào cache cho từng nhân viên.
        """
        from . import attendance_logic
        import time
        import logging
        _logger = logging.getLogger(__name__)
        
        if not self:
            return
            
        # Nhóm các dòng theo từng bảng cân đối tháng
        for month_id, records in self.grouped('month_id').items():
            if not month_id.date_month:
                continue
                
            metadata = attendance_logic.get_day_metadata(month_id.date_month)
            vals = {}
            
            t1 = time.time()
            for i in range(1, 32):
                data = metadata.get(i, {'is_sunday': False, 'week': 0, 'row': 0})
                vals[f'day_{i:02d}_is_sunday'] = data['is_sunday']
                vals[f'day_{i:02d}_week'] = data['week']
                vals[f'day_{i:02d}_row'] = data['row']
            t2 = time.time()
            _logger.info("=== _compute_day_metadata: Vòng lặp build vals dict mất %.6fs ===", t2 - t1)
                
            # Đẩy toàn bộ 93 giá trị vào cache cho từng record cùng lúc
            t3 = time.time()
            for rec in records:
                rec.update(vals)
            t4 = time.time()
            _logger.info("=== _compute_day_metadata: Vòng lặp update cache cho %d records mất %.6fs ===", len(records), t4 - t3)

    @api.constrains('day_01', 'day_02', 'day_03', 'day_04', 'day_05', 'day_06', 'day_07', 'day_08', 'day_09', 'day_10',
                    'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20',
                    'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31')
    def _check_shift_change(self):
        from . import attendance_logic
        for rec in self:
            is_error, day_idx = attendance_logic.check_shift_change_violation(rec)
            if is_error:
                raise ValidationError(_(
                    "Nhân viên %s: Lỗi quy tắc đổi ca tại ngày %02d-%02d. "
                    "Khi chuyển từ ca Đêm (Đ) sang ca Ngày (N), bắt buộc phải có ngày Đổi ca (ĐC) ở giữa."
                ) % (rec.employee_id.name, day_idx, day_idx+1))

    @api.constrains('day_01', 'day_02', 'day_03', 'day_04', 'day_05', 'day_06', 'day_07', 'day_08', 'day_09', 'day_10',
                    'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20',
                    'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31')
    def _check_sunday_attendance(self):
        from . import attendance_logic
        for rec in self:
            day_idx = attendance_logic.check_sunday_attendance_violation(rec)
            if day_idx:
                raise ValidationError(_("Ngày %02d là Chủ Nhật. Không được phép chấm công thường vào ngày này. Vui lòng chấm vào phần Làm thêm giờ.") % day_idx)

    @api.constrains('day_01', 'day_02', 'day_03', 'day_04', 'day_05', 'day_06', 'day_07', 'day_08', 'day_09', 'day_10',
                    'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20',
                    'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31',
                    'ot_day_01', 'ot_day_02', 'ot_day_03', 'ot_day_04', 'ot_day_05', 'ot_day_06', 'ot_day_07', 'ot_day_08', 'ot_day_09', 'ot_day_10',
                    'ot_day_11', 'ot_day_12', 'ot_day_13', 'ot_day_14', 'ot_day_15', 'ot_day_16', 'ot_day_17', 'ot_day_18', 'ot_day_19', 'ot_day_20',
                    'ot_day_21', 'ot_day_22', 'ot_day_23', 'ot_day_24', 'ot_day_25', 'ot_day_26', 'ot_day_27', 'ot_day_28', 'ot_day_29', 'ot_day_30', 'ot_day_31')
    def _check_departure_date_attendance(self):
        from . import attendance_logic
        for rec in self:
            vals_to_clear = attendance_logic.check_departure_date_violation(rec)
            if vals_to_clear:
                rec.sudo().write(vals_to_clear)

    def _compute_virtual_days(self):
        for rec in self:
            mapping = {} # slot_idx -> day_idx (1-31)
            for i in range(1, 32):
                w = getattr(rec, f'day_{i:02d}_week')
                r = getattr(rec, f'day_{i:02d}_row')
                if 1 <= w <= 6 and 1 <= r <= 7:
                    slot = (w - 1) * 7 + r
                    mapping[slot] = i
            
            for s in range(1, 43):
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
                if 1 <= w <= 6 and 1 <= r <= 7:
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
    def _inverse_v36(self): self._inverse_v_generic(36)
    def _inverse_v36_ot(self): self._inverse_v_generic(36, True)
    def _inverse_v37(self): self._inverse_v_generic(37)
    def _inverse_v37_ot(self): self._inverse_v_generic(37, True)
    def _inverse_v38(self): self._inverse_v_generic(38)
    def _inverse_v38_ot(self): self._inverse_v_generic(38, True)
    def _inverse_v39(self): self._inverse_v_generic(39)
    def _inverse_v39_ot(self): self._inverse_v_generic(39, True)
    def _inverse_v40(self): self._inverse_v_generic(40)
    def _inverse_v40_ot(self): self._inverse_v_generic(40, True)
    def _inverse_v41(self): self._inverse_v_generic(41)
    def _inverse_v41_ot(self): self._inverse_v_generic(41, True)
    def _inverse_v42(self): self._inverse_v_generic(42)
    def _inverse_v42_ot(self): self._inverse_v_generic(42, True)

    def action_open_quick_fix(self):
        """Mở Wizard Sửa nhanh công để giảm công thường/OT cho nhân viên bất thường."""
        self.ensure_one()
        return {
            'name': f'Sửa nhanh công - {self.employee_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'dl.salary.kpi.quick.fix.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_line_id': self.id,
                'default_employee_name': self.employee_name,
                'default_identification_id': self.identification_id,
                'default_current_lk': self.payroll_net_salary_base,
                'default_target_salary': self.payroll_internal_salary,
            }
        }

    # @api.constrains('payroll_bank_transfer_amount', 'payroll_internal_salary')
    # def _check_bank_transfer_limit(self):
    #     for rec in self:
    #         # Chỉ kiểm tra nếu có lương nội bộ (tránh lỗi khi chưa nhập Ln)
    #         if rec.payroll_internal_salary > 0 and rec.payroll_bank_transfer_amount > rec.payroll_internal_salary:
    #             # Tính toán chênh lệch để thông báo rõ ràng
    #             diff = rec.payroll_bank_transfer_amount - rec.payroll_internal_salary
    #             def fmt(v): return "{:,.0f}".format(v).replace(",", ".")
    #             
    #             raise ValidationError(_(
    #                 "Dòng của %s: Tiền chuyển khoản (%s) đang cao hơn Lương nội bộ (%s) một khoảng %s. \n\n"
    #                 "Lý do: Thực lĩnh ngoài (Lk) hoặc KPI (Mk) quá cao. \n"
    #                 "Giải pháp: Hãy dùng nút 'Sửa nhanh' để giảm bớt ngày công hoặc giảm điểm KPI."
    #             ) % (rec.employee_name, fmt(rec.payroll_bank_transfer_amount), fmt(rec.payroll_internal_salary), fmt(diff)))
