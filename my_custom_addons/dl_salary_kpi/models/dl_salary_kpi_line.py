# -*- coding: utf-8 -*-
import math
import random
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SalaryKpiLine(models.Model):
    _name = 'dl.salary.kpi.line'
    _description = 'Dòng chấm công tháng'
    _order = 'dl_tax_department_sequence, dl_first_name'

    month_id = fields.Many2one('dl.salary.kpi.month', string='Tháng bảng công', ondelete='cascade')
    month_state = fields.Selection(related='month_id.state', string='Trạng thái tháng', store=True)
    company_id = fields.Many2one('res.company', string='Công ty', related='month_id.company_id', store=True, readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True)
    employee_name = fields.Char(related='employee_id.name', string='Tên nhân viên', store=True)
    dl_first_name = fields.Char(related='employee_id.dl_first_name', string='Tên riêng', store=True)
    identification_id = fields.Char(related='employee_id.identification_id', string='Số CCCD', store=True)
    
    dl_tax_department_id = fields.Many2one('dl.tax.department', related='employee_id.dl_tax_department_id', string='Phòng ban', store=True, help="Phòng ban hoặc bộ phận quản lý thuế/bảo hiểm của nhân viên. Dùng để phân loại khi xuất báo cáo thuế TNCN.")
    dl_tax_department_sequence = fields.Integer(related='dl_tax_department_id.sequence', string='Thứ tự phòng ban', store=True)
    dl_tax_id = fields.Char(related='employee_id.dl_tax_id', string='Mã số thuế', store=True)
    birthday = fields.Date(related='employee_id.birthday', string='Ngày sinh')
    sex = fields.Selection(related='employee_id.sex', string='Giới tính')
    dl_tax_position = fields.Char(related='employee_id.dl_tax_position', string='Chức vụ')
    dl_tax_base_salary = fields.Float(related='employee_id.dl_tax_base_salary', string='Lương cơ bản', help="Mức lương căn cứ để tính đóng BHXH và thuế TNCN (Lương chính quy trên hợp đồng lao động).")


    # Chấm công 31 ngày (hiển thị mã công)
    day_01 = fields.Many2one('dl.salary.kpi.attendance.type', string='01', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_02 = fields.Many2one('dl.salary.kpi.attendance.type', string='02', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_03 = fields.Many2one('dl.salary.kpi.attendance.type', string='03', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_04 = fields.Many2one('dl.salary.kpi.attendance.type', string='04', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_05 = fields.Many2one('dl.salary.kpi.attendance.type', string='05', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_06 = fields.Many2one('dl.salary.kpi.attendance.type', string='06', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_07 = fields.Many2one('dl.salary.kpi.attendance.type', string='07', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_08 = fields.Many2one('dl.salary.kpi.attendance.type', string='08', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_09 = fields.Many2one('dl.salary.kpi.attendance.type', string='09', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_10 = fields.Many2one('dl.salary.kpi.attendance.type', string='10', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_11 = fields.Many2one('dl.salary.kpi.attendance.type', string='11', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_12 = fields.Many2one('dl.salary.kpi.attendance.type', string='12', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_13 = fields.Many2one('dl.salary.kpi.attendance.type', string='13', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_14 = fields.Many2one('dl.salary.kpi.attendance.type', string='14', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_15 = fields.Many2one('dl.salary.kpi.attendance.type', string='15', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_16 = fields.Many2one('dl.salary.kpi.attendance.type', string='16', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_17 = fields.Many2one('dl.salary.kpi.attendance.type', string='17', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_18 = fields.Many2one('dl.salary.kpi.attendance.type', string='18', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_19 = fields.Many2one('dl.salary.kpi.attendance.type', string='19', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_20 = fields.Many2one('dl.salary.kpi.attendance.type', string='20', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_21 = fields.Many2one('dl.salary.kpi.attendance.type', string='21', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_22 = fields.Many2one('dl.salary.kpi.attendance.type', string='22', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_23 = fields.Many2one('dl.salary.kpi.attendance.type', string='23', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_24 = fields.Many2one('dl.salary.kpi.attendance.type', string='24', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_25 = fields.Many2one('dl.salary.kpi.attendance.type', string='25', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_26 = fields.Many2one('dl.salary.kpi.attendance.type', string='26', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_27 = fields.Many2one('dl.salary.kpi.attendance.type', string='27', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_28 = fields.Many2one('dl.salary.kpi.attendance.type', string='28', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_29 = fields.Many2one('dl.salary.kpi.attendance.type', string='29', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_30 = fields.Many2one('dl.salary.kpi.attendance.type', string='30', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    day_31 = fields.Many2one('dl.salary.kpi.attendance.type', string='31', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")

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
    v01 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v01', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v01_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v01_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v01_label = fields.Char(compute='_compute_virtual_days')
    v01_sun = fields.Boolean(compute='_compute_virtual_days')
    v02 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v02', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v02_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v02_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v02_label = fields.Char(compute='_compute_virtual_days')
    v02_sun = fields.Boolean(compute='_compute_virtual_days')
    v03 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v03', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v03_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v03_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v03_label = fields.Char(compute='_compute_virtual_days')
    v03_sun = fields.Boolean(compute='_compute_virtual_days')
    v04 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v04', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v04_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v04_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v04_label = fields.Char(compute='_compute_virtual_days')
    v04_sun = fields.Boolean(compute='_compute_virtual_days')
    v05 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v05', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v05_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v05_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v05_label = fields.Char(compute='_compute_virtual_days')
    v05_sun = fields.Boolean(compute='_compute_virtual_days')
    v06 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v06', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v06_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v06_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v06_label = fields.Char(compute='_compute_virtual_days')
    v06_sun = fields.Boolean(compute='_compute_virtual_days')
    v07 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v07', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v07_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v07_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v07_label = fields.Char(compute='_compute_virtual_days')
    v07_sun = fields.Boolean(compute='_compute_virtual_days')
    v08 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v08', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v08_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v08_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v08_label = fields.Char(compute='_compute_virtual_days')
    v08_sun = fields.Boolean(compute='_compute_virtual_days')
    v09 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v09', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v09_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v09_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v09_label = fields.Char(compute='_compute_virtual_days')
    v09_sun = fields.Boolean(compute='_compute_virtual_days')
    v10 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v10', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v10_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v10_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v10_label = fields.Char(compute='_compute_virtual_days')
    v10_sun = fields.Boolean(compute='_compute_virtual_days')
    v11 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v11', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v11_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v11_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v11_label = fields.Char(compute='_compute_virtual_days')
    v11_sun = fields.Boolean(compute='_compute_virtual_days')
    v12 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v12', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v12_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v12_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v12_label = fields.Char(compute='_compute_virtual_days')
    v12_sun = fields.Boolean(compute='_compute_virtual_days')
    v13 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v13', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v13_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v13_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v13_label = fields.Char(compute='_compute_virtual_days')
    v13_sun = fields.Boolean(compute='_compute_virtual_days')
    v14 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v14', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v14_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v14_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v14_label = fields.Char(compute='_compute_virtual_days')
    v14_sun = fields.Boolean(compute='_compute_virtual_days')
    v15 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v15', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v15_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v15_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v15_label = fields.Char(compute='_compute_virtual_days')
    v15_sun = fields.Boolean(compute='_compute_virtual_days')
    v16 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v16', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v16_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v16_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v16_label = fields.Char(compute='_compute_virtual_days')
    v16_sun = fields.Boolean(compute='_compute_virtual_days')
    v17 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v17', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v17_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v17_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v17_label = fields.Char(compute='_compute_virtual_days')
    v17_sun = fields.Boolean(compute='_compute_virtual_days')
    v18 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v18', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v18_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v18_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v18_label = fields.Char(compute='_compute_virtual_days')
    v18_sun = fields.Boolean(compute='_compute_virtual_days')
    v19 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v19', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v19_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v19_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v19_label = fields.Char(compute='_compute_virtual_days')
    v19_sun = fields.Boolean(compute='_compute_virtual_days')
    v20 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v20', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v20_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v20_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v20_label = fields.Char(compute='_compute_virtual_days')
    v20_sun = fields.Boolean(compute='_compute_virtual_days')
    v21 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v21', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v21_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v21_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v21_label = fields.Char(compute='_compute_virtual_days')
    v21_sun = fields.Boolean(compute='_compute_virtual_days')
    v22 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v22', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v22_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v22_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v22_label = fields.Char(compute='_compute_virtual_days')
    v22_sun = fields.Boolean(compute='_compute_virtual_days')
    v23 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v23', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v23_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v23_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v23_label = fields.Char(compute='_compute_virtual_days')
    v23_sun = fields.Boolean(compute='_compute_virtual_days')
    v24 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v24', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v24_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v24_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v24_label = fields.Char(compute='_compute_virtual_days')
    v24_sun = fields.Boolean(compute='_compute_virtual_days')
    v25 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v25', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v25_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v25_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v25_label = fields.Char(compute='_compute_virtual_days')
    v25_sun = fields.Boolean(compute='_compute_virtual_days')
    v26 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v26', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v26_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v26_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v26_label = fields.Char(compute='_compute_virtual_days')
    v26_sun = fields.Boolean(compute='_compute_virtual_days')
    v27 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v27', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v27_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v27_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v27_label = fields.Char(compute='_compute_virtual_days')
    v27_sun = fields.Boolean(compute='_compute_virtual_days')
    v28 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v28', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v28_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v28_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v28_label = fields.Char(compute='_compute_virtual_days')
    v28_sun = fields.Boolean(compute='_compute_virtual_days')
    v29 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v29', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v29_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v29_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v29_label = fields.Char(compute='_compute_virtual_days')
    v29_sun = fields.Boolean(compute='_compute_virtual_days')
    v30 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v30', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v30_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v30_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v30_label = fields.Char(compute='_compute_virtual_days')
    v30_sun = fields.Boolean(compute='_compute_virtual_days')
    v31 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v31', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v31_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v31_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v31_label = fields.Char(compute='_compute_virtual_days')
    v31_sun = fields.Boolean(compute='_compute_virtual_days')
    v32 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v32', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v32_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v32_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v32_label = fields.Char(compute='_compute_virtual_days')
    v32_sun = fields.Boolean(compute='_compute_virtual_days')
    v33 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v33', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v33_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v33_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v33_label = fields.Char(compute='_compute_virtual_days')
    v33_sun = fields.Boolean(compute='_compute_virtual_days')
    v34 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v34', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v34_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v34_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v34_label = fields.Char(compute='_compute_virtual_days')
    v34_sun = fields.Boolean(compute='_compute_virtual_days')
    v35 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v35', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v35_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v35_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v35_label = fields.Char(compute='_compute_virtual_days')
    v35_sun = fields.Boolean(compute='_compute_virtual_days')
    v36 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v36', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v36_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v36_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v36_label = fields.Char(compute='_compute_virtual_days')
    v36_sun = fields.Boolean(compute='_compute_virtual_days')
    v37 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v37', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v37_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v37_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v37_label = fields.Char(compute='_compute_virtual_days')
    v37_sun = fields.Boolean(compute='_compute_virtual_days')
    v38 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v38', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v38_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v38_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v38_label = fields.Char(compute='_compute_virtual_days')
    v38_sun = fields.Boolean(compute='_compute_virtual_days')
    v39 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v39', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v39_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v39_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v39_label = fields.Char(compute='_compute_virtual_days')
    v39_sun = fields.Boolean(compute='_compute_virtual_days')
    v40 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v40', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v40_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v40_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v40_label = fields.Char(compute='_compute_virtual_days')
    v40_sun = fields.Boolean(compute='_compute_virtual_days')
    v41 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v41', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v41_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v41_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    v41_label = fields.Char(compute='_compute_virtual_days')
    v41_sun = fields.Boolean(compute='_compute_virtual_days')
    v42 = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v42', domain="[('apply_to', 'in', ['normal', 'both']), ('company_id', '=', company_id)]")
    v42_ot = fields.Many2one('dl.salary.kpi.attendance.type', compute='_compute_virtual_days', inverse='_inverse_v42_ot', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
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
    ot_day_01 = fields.Many2one('dl.salary.kpi.attendance.type', string='01', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_02 = fields.Many2one('dl.salary.kpi.attendance.type', string='02', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_03 = fields.Many2one('dl.salary.kpi.attendance.type', string='03', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_04 = fields.Many2one('dl.salary.kpi.attendance.type', string='04', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_05 = fields.Many2one('dl.salary.kpi.attendance.type', string='05', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_06 = fields.Many2one('dl.salary.kpi.attendance.type', string='06', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_07 = fields.Many2one('dl.salary.kpi.attendance.type', string='07', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_08 = fields.Many2one('dl.salary.kpi.attendance.type', string='08', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_09 = fields.Many2one('dl.salary.kpi.attendance.type', string='09', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_10 = fields.Many2one('dl.salary.kpi.attendance.type', string='10', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_11 = fields.Many2one('dl.salary.kpi.attendance.type', string='11', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_12 = fields.Many2one('dl.salary.kpi.attendance.type', string='12', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_13 = fields.Many2one('dl.salary.kpi.attendance.type', string='13', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_14 = fields.Many2one('dl.salary.kpi.attendance.type', string='14', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_15 = fields.Many2one('dl.salary.kpi.attendance.type', string='15', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_16 = fields.Many2one('dl.salary.kpi.attendance.type', string='16', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_17 = fields.Many2one('dl.salary.kpi.attendance.type', string='17', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_18 = fields.Many2one('dl.salary.kpi.attendance.type', string='18', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_19 = fields.Many2one('dl.salary.kpi.attendance.type', string='19', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_20 = fields.Many2one('dl.salary.kpi.attendance.type', string='20', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_21 = fields.Many2one('dl.salary.kpi.attendance.type', string='21', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_22 = fields.Many2one('dl.salary.kpi.attendance.type', string='22', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_23 = fields.Many2one('dl.salary.kpi.attendance.type', string='23', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_24 = fields.Many2one('dl.salary.kpi.attendance.type', string='24', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_25 = fields.Many2one('dl.salary.kpi.attendance.type', string='25', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_26 = fields.Many2one('dl.salary.kpi.attendance.type', string='26', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_27 = fields.Many2one('dl.salary.kpi.attendance.type', string='27', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_28 = fields.Many2one('dl.salary.kpi.attendance.type', string='28', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_29 = fields.Many2one('dl.salary.kpi.attendance.type', string='29', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_30 = fields.Many2one('dl.salary.kpi.attendance.type', string='30', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")
    ot_day_31 = fields.Many2one('dl.salary.kpi.attendance.type', string='31', domain="[('apply_to', 'in', ['overtime', 'both']), ('company_id', '=', company_id)]")

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
    bonus_p_day = fields.Float(string='Thưởng chuyên cần', compute='_compute_totals', store=True, help="Nếu làm từ 20 công (Ngày + Đêm) trở lên sẽ được tặng 1 công phép (Công N/2, Đ/2 tính 0.5 công).")
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
    payroll_wage_day_exp = fields.Char(string='Diễn giải lương ngày', compute='_compute_payroll_internal', store=True)
    
    payroll_wage_day_150 = fields.Monetary(string='Lương TC ngày 150%', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_wage_day_150_exp = fields.Char(string='Diễn giải TC ngày 150%', compute='_compute_payroll_internal', store=True)
    
    payroll_wage_night_130 = fields.Monetary(string='Lương ca đêm thường 130%', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_wage_night_130_exp = fields.Char(string='Diễn giải ca đêm 130%', compute='_compute_payroll_internal', store=True)
    
    payroll_wage_night_200 = fields.Monetary(string='Lương TC đêm 200% (Ko ngày)', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_wage_night_200_exp = fields.Char(string='Diễn giải TC đêm 200%', compute='_compute_payroll_internal', store=True)
    
    payroll_wage_night_210 = fields.Monetary(string='Lương TC đêm 210% (Có ngày)', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_wage_night_210_exp = fields.Char(string='Diễn giải TC đêm 210%', compute='_compute_payroll_internal', store=True)
    
    payroll_wage_night_sun_270 = fields.Monetary(string='Lương TC đêm CN 270%', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_wage_night_sun_270_exp = fields.Char(string='Diễn giải TC đêm CN 270%', compute='_compute_payroll_internal', store=True)
    
    payroll_wage_day_sun_200 = fields.Monetary(string='Lương CN ca ngày 200%', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_wage_day_sun_200_exp = fields.Char(string='Diễn giải CN ca ngày 200%', compute='_compute_payroll_internal', store=True)
    
    payroll_wage_day_holiday_300 = fields.Monetary(string='Lương Lễ ca ngày 300%', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_wage_day_holiday_300_exp = fields.Char(string='Diễn giải Lễ ca ngày 300%', compute='_compute_payroll_internal', store=True)
    
    payroll_wage_night_holiday_390 = fields.Monetary(string='Lương TC đêm Lễ 390%', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_wage_night_holiday_390_exp = fields.Char(string='Diễn giải TC đêm Lễ 390%', compute='_compute_payroll_internal', store=True)
    
    payroll_revenue_bonus_exp = fields.Char(string='Diễn giải thưởng doanh thu', compute='_compute_payroll_internal', store=True)
    payroll_productivity_bonus_exp = fields.Char(string='Diễn giải thưởng năng suất', compute='_compute_payroll_internal', store=True)
    payroll_meal_allowance_exp = fields.Char(string='Diễn giải ăn ca', compute='_compute_payroll_internal', store=True)
    payroll_women_allowance_exp = fields.Char(string='Diễn giải phụ cấp phụ nữ', compute='_compute_payroll_internal', store=True)
    
    payroll_total_wage = fields.Monetary(string='Tổng lương', compute='_compute_payroll_internal', store=True, currency_field='currency_id', help="Tổng lương = Tổng các khoản lương chi tiết (ngày, đêm, tăng ca...) + Thưởng doanh thu thực tế")
    payroll_total_actual_income = fields.Monetary(string='Tổng TN T.tế', compute='_compute_payroll_internal', store=True, currency_field='currency_id', help="Tổng thu nhập thực tế = Tổng lương + Các khoản trợ cấp thực tế (đã tỷ lệ theo công) + Tiền KPI")
    payroll_real_net_income = fields.Monetary(string='Thực lĩnh thực tế', compute='_compute_payroll_internal', store=True, currency_field='currency_id', help="Thực lĩnh thực tế = Tổng thu nhập thực tế - Tổng các khoản khấu trừ")

    # --- CÁC KHOẢN KHẤU TRỪ ---
    payroll_deduction_bhxh = fields.Monetary(string='BHXH (8%)', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_deduction_bhyt = fields.Monetary(string='BHYT (1.5%)', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_deduction_bhtn = fields.Monetary(string='BHTN (1%)', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_deduction_tncn = fields.Monetary(string='Thuế TNCN', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_total_insurance_deduction = fields.Monetary(string='Tổng cộng trừ bảo hiểm', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    
    # --- CÁC TRƯỜNG PHỤC VỤ THUẾ TNCN ---
    payroll_pit_taxable_income = fields.Monetary(string='Thu nhập chịu thuế (TNCT)', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_pit_taxable_explanation = fields.Html(string='Diễn giải TNCT', compute='_compute_payroll_internal', store=True)
    payroll_pit_number_of_dependents = fields.Integer(string='Số người phụ thuộc', compute='_compute_payroll_internal', store=True)
    payroll_pit_total_deductions = fields.Monetary(string='Tổng các khoản giảm trừ', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_pit_assessable_income = fields.Monetary(string='Thu nhập tính thuế (TNTT)', compute='_compute_payroll_internal', store=True, currency_field='currency_id')

    payroll_total_deduction = fields.Monetary(string='Tổng các khoản trừ', compute='_compute_payroll_internal', store=True, currency_field='currency_id')
    payroll_net_salary_base = fields.Monetary(string='Thực lĩnh ngoài(TLN)', compute='_compute_payroll_internal', store=True, currency_field='currency_id', aggregator='sum', help="Tổng thu nhập thực tế dựa trên năng suất sản phẩm (Lương khoán).")
    payroll_net_salary = fields.Monetary(string='Thực lĩnh cuối cùng', compute='_compute_payroll_internal', store=True, currency_field='currency_id', aggregator='sum')

    # --- TỰ ĐỘNG SINH ĐIỂM KPI ---
    payroll_internal_salary = fields.Monetary(string='Lương Nội Bộ (LNB)', currency_field='currency_id', aggregator='sum', help="Lương thực tế muốn trả cho nhân viên (Target Salary)")
    payroll_internal_salary_minus_bonus = fields.Monetary(string='LNB trừ thưởng năm', compute='_compute_payroll_internal', store=True, currency_field='currency_id', aggregator='sum')
    payroll_kpi_score = fields.Float(string='Điểm KPI (Sinh ra)', digits=(16, 2), aggregator="avg")
    payroll_kpi_amount = fields.Monetary(string='Tiền KPI (Cân đối)', currency_field='currency_id', aggregator='sum')
    payroll_kpi_amount_rounded = fields.Monetary(string='Tiền KPI làm tròn', currency_field='currency_id', aggregator='sum')
    payroll_kpi_amount_rounding_error = fields.Monetary(string='Sai số KPI', currency_field='currency_id', aggregator='sum')
    payroll_cash_amount = fields.Monetary(string='Tiền mặt trả thêm', currency_field='currency_id', aggregator='sum')
    
    payroll_bank_transfer_amount = fields.Monetary(
        string='Tiền chuyển khoản', 
        compute='_compute_payroll_internal', 
        store=True, 
        currency_field='currency_id', 
        aggregator='sum',
        help="Tổng số tiền thực tế sẽ chuyển khoản cho nhân viên. Bao gồm: Thực lĩnh ngoài(TLN) + Tiền KPI + Thưởng lễ tết (nếu có)."
    )
    payroll_bank_transfer_amount_rounded = fields.Monetary(string='Tiền CK làm tròn', compute='_compute_payroll_internal', store=True, currency_field='currency_id', aggregator='sum')
    payroll_bank_transfer_amount_rounding_error = fields.Monetary(string='Sai số CK', compute='_compute_payroll_internal', store=True, currency_field='currency_id', aggregator='sum')
    payroll_tracking_percentage = fields.Float(
        string='Theo Dõi %', 
        compute='_compute_payroll_tracking_percentage', 
        store=True,
        help='Phần trăm tiền chuyển khoản so với lương cơ bản thuế'
    )
    payroll_cash_amount_rounded = fields.Monetary(string='Tiền mặt làm tròn', compute='_compute_payroll_internal', store=True, currency_field='currency_id', aggregator='sum')
    payroll_cash_amount_rounding_error = fields.Monetary(string='Sai số Tiền mặt', compute='_compute_payroll_internal', store=True, currency_field='currency_id', aggregator='sum')

    # --- QUẢN LÝ DỮ LIỆU BẤT THƯỜNG ---
    x_has_anomaly = fields.Boolean(string='Từng có bất thường', default=False, copy=False, help="Đánh dấu nếu bản ghi này đã từng hoặc đang gặp lỗi dữ liệu (TLN > Ln, KPI âm, Cash lẻ...)")
    x_is_anomaly_resolved = fields.Boolean(string='Đã cân đối xong', default=False, copy=False)
    x_sequence = fields.Integer(string='STT')

    def action_toggle_anomaly_resolved(self):
        for rec in self:
            rec.x_is_anomaly_resolved = not rec.x_is_anomaly_resolved
            if rec.x_is_anomaly_resolved:
                # Khi người dùng chủ động bấm xác nhận, ta xóa Flag "Neo" để ẩn khỏi tab
                rec.x_has_anomaly = False
    total_normal_weekday_days = fields.Integer(string='Tổng công thường T2-T7', compute='_compute_payroll_internal', store=True)

    payroll_anomaly_suggestion = fields.Html(string='Gợi ý xử lý', compute='_compute_payroll_internal', store=True)
    payroll_income_explanation = fields.Html(string='Diễn giải thu nhập', compute='_compute_payroll_internal', store=True)
    payroll_calc_detail_html = fields.Html(string='Chi tiết tính toán KPI & Tiền mặt', compute='_compute_payroll_calc_detail')

    @api.depends('payroll_net_salary_base', 'payroll_kpi_amount', 'payroll_cash_amount', 'payroll_internal_salary', 'payroll_annual_bonus')
    def _compute_payroll_calc_detail(self):
        for rec in self:
            ck_tron = rec.payroll_bank_transfer_amount_rounded or 0
            tm_tron = rec.payroll_cash_amount_rounded or 0
            tong_nhan = ck_tron + tm_tron
            
            lnb = rec.payroll_internal_salary or 0
            tln = rec.payroll_net_salary_base or 0
            kpi_amount = rec.payroll_kpi_amount or 0
            annual_bonus = rec.payroll_annual_bonus or 0
            meal = rec.payroll_meal_allowance or 0
            women = rec.payroll_women_allowance or 0
            
            # --- TÍNH TOÁN ĐỐI SOÁT LNB ---
            # 1. Cân đối LNB (Chỉ trừ Thưởng năm)
            gap_lnb = (lnb - annual_bonus) - tln
            max_mk = tln * 0.4 # Giả định max 70 điểm là bù thêm 40% TLN
            
            # 2. LNB Thực nhận (sau làm tròn) = Tổng nhận - Ăn ca - Phụ cấp PN
            lnb_thuc_nhan = tong_nhan - meal - women
            chenh_lech_lnb = lnb_thuc_nhan - lnb
            
            reason = []
            if abs(chenh_lech_lnb) > 0 and abs(chenh_lech_lnb) < 2000:
                reason.append("Do làm tròn hàng nghìn (Round down) ở cả Tiền mặt và Chuyển khoản.")
            if rec.payroll_kpi_score >= 69.9:
                reason.append("Đã chạm trần KPI tối đa (70 điểm), phần còn lại được chuyển sang Tiền mặt.")
                
            style_color = "color: #28a745;" if abs(chenh_lech_lnb) < 2000 else "color: #dc3545;"
            
            # --- TÍNH TOÁN ĐỐI SOÁT ---
            # So sánh TLN (Công thực tế) và LNB (Tổng nhận cuối cùng)
            chenh_lech_tong = lnb - tln
            
            html = f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 14px; border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; background-color: #f8f9fa; margin-top: 15px; width: 100%;">
                <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 300px;">
                        <table class="table table-sm table-bordered bg-white">
                            <tr class="bg-primary text-white"><th colspan="2" class="p-2">1. CƠ SỞ ĐỐI SOÁT (TLN vs LNB)</th></tr>
                            <tr><td>Thực lĩnh ngoài thực tế (TLN)</td><td class="text-end"><b>{tln:,.0f}</b></td></tr>
                            <tr><td>Lương Nội Bộ mục tiêu (LNB)</td><td class="text-end"><b>{lnb:,.0f}</b></td></tr>
                            <tr class="table-warning"><td><b>Chênh lệch cần bù (LNB - TLN)</b></td><td class="text-end"><b>{chenh_lech_tong:,.0f}</b></td></tr>
                        </table>
                        <div class="text-muted" style="font-size: 11px;">
                            <i>* Đây là số tiền công ty bù thêm cho nhân viên ngoài lương thực tế làm được.</i>
                        </div>
                    </div>
                    <div style="flex: 1; min-width: 300px;">
                        <table class="table table-sm table-bordered bg-white">
                            <tr class="bg-success text-white"><th colspan="2" class="p-2">2. CHI TIẾT DÒNG TIỀN CHI TRẢ</th></tr>
                            <tr><td>Tiền KPI (Phần chính)</td><td class="text-end">{kpi_amount:,.0f}</td></tr>
                            <tr><td>Thưởng Lễ/Tết (Nếu có)</td><td class="text-end">{annual_bonus:,.0f}</td></tr>
                            <tr class="table-info"><td><b>Tổng Chuyển Khoản (Đã tròn)</b></td><td class="text-end"><b>{ck_tron:,.0f}</b></td></tr>
                            <tr class="table-danger"><td><b>Tổng Tiền Mặt (Đã tròn)</b></td><td class="text-end"><b>{tm_tron:,.0f}</b></td></tr>
                        </table>
                        <div class="text-muted" style="font-size: 11px;">
                            <i>* Tiền mặt = LNB - Tiền chuyển khoản. Bao gồm các khoản trợ cấp và phần bù dư.</i>
                        </div>
                    </div>
                </div>

                <div style="margin-top: 15px; background-color: #fff; border: 1px dashed #007bff; border-radius: 6px; padding: 10px;">
                    <b style="color: #0056b3;">🔍 QUY TRÌNH TÍNH TOÁN &amp; ĐỐI SOÁT:</b>
                    <div style="display: flex; gap: 10px; margin-top: 8px; font-size: 13px;">
                        <div style="flex: 1; border-right: 1px solid #eee; padding-right: 10px;">
                            <b style="color: #666;">BƯỚC 1: Tính Tiền KPI</b><br/>
                            Gap = (LNB - Thưởng) - TLN<br/>
                            = {gap_lnb:,.0f}<br/>
                            => KPI = {kpi_amount:,.0f} ({rec.payroll_kpi_score}đ)
                        </div>
                        <div style="flex: 1; border-right: 1px solid #eee; padding-right: 10px;">
                            <b style="color: #666;">BƯỚC 2: Tính Chuyển Khoản</b><br/>
                            CK = TLN + KPI + Thưởng<br/>
                            = {ck_tron:,.0f} (Đã làm tròn)
                        </div>
                        <div style="flex: 1;">
                            <b style="color: #666;">BƯỚC 3: Tính Tiền Mặt</b><br/>
                            TM = LNB - Chuyển Khoản<br/>
                            = {lnb:,.0f} - {ck_tron:,.0f}<br/>
                            = <b style="color: #d32f2f;">{tm_tron:,.0f}</b>
                        </div>
                    </div>
                </div>

                <div style="margin-top: 15px;">
                    <table class="table table-bordered bg-white m-0 text-center">
                        <tr class="table-dark">
                            <td class="p-2" style="width: 25%;"><b>TỔNG THỰC NHẬN (CK + TM)</b></td>
                            <td class="text-end p-2" style="width: 25%; font-size: 18px;"><b>{tong_nhan:,.0f}</b></td>
                            <td class="p-2" style="width: 25%;"><b>MỤC TIÊU LNB</b></td>
                            <td class="text-end p-2" style="width: 25%; font-size: 18px;"><b>{lnb:,.0f}</b></td>
                        </tr>
                    </table>
                </div>
            </div>
            """
            rec.payroll_calc_detail_html = html



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
            
            # Lấy LNB trừ đi Thưởng năm và TLN để tìm phần còn thiếu cần bù KPI/Tiền mặt
            lk = rec.payroll_net_salary_base
            # Gap là phần còn thiếu để đạt được (LNB - Thưởng năm TIỀM NĂNG)
            # Theo yêu cầu: LNB đã bao gồm Thưởng năm. Ta dùng LNB trừ thưởng tiềm năng để giữ Gap ổn định.
            gap = rec.payroll_internal_salary_minus_bonus - lk
            
            if rec.payroll_internal_salary_minus_bonus <= 0 or lk <= 0:
                rec.write({'payroll_kpi_score': 0, 'payroll_kpi_amount': 0, 'payroll_cash_amount': 0})
                continue
            # --- KIỂM SOÁT ĐIỂM TỐI THIỂU & TỐI ĐA THEO LƯƠNG CƠ BẢN ---
            base_salary = rec.dl_tax_base_salary
            if base_salary < 4500000:
                emp_max_kpi = min(55.0, float(max_allowed))
                emp_min_kpi = 50.0
            elif base_salary < 5000000:
                emp_max_kpi = min(60.0, float(max_allowed))
                emp_min_kpi = 55.0
            else:
                emp_max_kpi = min(70.0, float(max_allowed))
                emp_min_kpi = 60.0
                
            # Đảm bảo max_allowed không nhỏ hơn 50
            emp_max_kpi = max(50.0, emp_max_kpi)
            emp_min_kpi = min(emp_min_kpi, emp_max_kpi)

            emp_max_mk = lk * (emp_max_kpi - 50.0) / 50.0
            
            if gap <= 0:
                p_final = 50.0
                mk = 0.0
                cash = 0.0
            elif gap <= emp_max_mk:
                # Đủ sức dùng 100% KPI (Không dùng Tiền mặt)
                # Cho phép điểm KPI lẻ để khớp hoàn toàn Ln = TLN + Mk
                p_final = 50.0 + 50.0 * gap / lk
                mk = gap
                cash = 0.0
            else:
                # Bắt buộc dùng Tiền mặt
                cash_needed = gap - emp_max_mk
                if cash_needed >= 1000000:
                    # Tiền mặt đủ lớn, lấy ngẫu nhiên Điểm KPI
                    p_temp = random.uniform(emp_min_kpi, float(emp_max_kpi))
                    
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
                        p_upper = min(emp_max_kpi, p_upper)
                        effective_min = min(emp_min_kpi, p_upper)
                        
                        p_temp = random.uniform(float(effective_min), float(p_upper))
                        
                        mk_temp = lk * (p_temp - 50.0) / 50.0
                        cash_raw = gap - mk_temp
                        # Làm tròn Tiền mặt đến hàng chục nghìn (10.000 VNĐ)
                        cash = round(cash_raw / 10000.0) * 10000
                        mk = gap - cash
                        p_final = 50.0 + 50.0 * mk / lk
                
                # --- KIỂM SOÁT BIÊN (CAPPING) ---
                # Nếu sau khi làm tròn mà p_final vượt ngưỡng cho phép
                if p_final > emp_max_kpi:
                    p_final = float(emp_max_kpi)
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
            
            write_vals = {
                'payroll_kpi_score': p_final,
                'payroll_kpi_amount': mk,
                'payroll_cash_amount': cash,
                'kpi_c1_productivity': kpi_vals[0],
                'kpi_c2_discipline': kpi_vals[1],
                'kpi_c3_teamwork': kpi_vals[2],
                'kpi_c4_5s': kpi_vals[3],
                'kpi_c5_saving': kpi_vals[4],
            }
            
            # --- LOGIC NEO DỮ LIỆU BẤT THƯỜNG (STICKY FLAG) ---
            # Chỉ gán cờ bất thường khi Tạo KPI (đủ dữ liệu)
            is_currently_anomaly = (rec.payroll_internal_salary > 0 and lk > rec.payroll_internal_salary) \
                                   or (rec.month_id.x_has_imported_internal_salary and rec.month_id.x_is_recalculated and rec.payroll_internal_salary == 0 and lk > 0) \
                                   or mk < -1 \
                                   or (0 < cash < 1000000)
            
            if is_currently_anomaly:
                write_vals['x_has_anomaly'] = True
                write_vals['x_is_anomaly_resolved'] = False
                
            rec.write(write_vals)
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
            
            # 2. Thưởng cố định năm (Chỉ lấy Thực tế dựa trên công)
            act_bonus, pot_bonus = payroll_logic.calculate_annual_bonuses(rec)
            
            b0803 = act_bonus['b0803']
            b3004 = act_bonus['b3004']
            b0209 = act_bonus['b0209']
            btet = act_bonus['btet']
            bother = act_bonus['bother']
            annual_bonus = b0803 + b3004 + b0209 + btet + bother
            
            # 3. Thưởng doanh thu & Năng suất (Theo chính sách QĐ 3108)
            revenue_bonus, productivity_bonus, rev_bonus_base, prod_bonus_base = payroll_logic.calculate_revenue_productivity_bonuses(rec)
            
            # Tổng trợ cấp & thưởng năm = Ăn ca + Phụ cấp phụ nữ
            total_bonus = meal_allowance + women_allowance
            
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
            
            # Tính toán số tiền được miễn thuế (Miễn 100% cho OT, Lương phép và Chuyên cần)
            exempt_ot_amount = (
                wages['wage_day_150'] +
                wages['wage_night_130'] +
                wages['wage_night_200'] +
                wages['wage_night_sun_270'] +
                wages['wage_day_sun_200'] +
                wages['wage_day_holiday_300'] +
                wages['wage_night_holiday_390'] +
                wages['wage_leave'] +
                wages['wage_bonus_p']
            )

            # --- PHẦN TÍNH TOÁN TLN VÀ TỔNG THU NHẬP THỰC TẾ (LOGIC MỚI) ---
            # 1. Gross TLN (Tổng lương & Thưởng hiệu quả chính quy)
            gross_lk = total_detailed_wage + revenue_bonus + productivity_bonus
            
            # 2. Thực lĩnh ngoài(TLN) = Gross TLN (KHÔNG KHẤU TRỪ theo yêu cầu)
            net_salary_base = gross_lk
            
            # 3. Tổng thu nhập thực tế = TLN + Ăn ca + Phụ cấp phụ nữ + Tiền KPI (Nếu có)
            total_actual_income = net_salary_base + meal_allowance + women_allowance + max(0, rec.payroll_kpi_amount or 0)

            # --- PHẦN TÍNH TOÁN THUẾ VÀ KHẤU TRỪ (Mới: Dựa trên Tổng TN thực tế + Thưởng năm) ---
            # Thu nhập chịu thuế cơ sở = Tổng TN Thực tế + Thưởng Năm
            base_income_for_tax = total_actual_income + annual_bonus
            deductions = payroll_logic.calculate_deductions(rec, base_income_for_tax, meal_allowance)
            
            # Cập nhật TNCT chuẩn sau khi trừ phần miễn thuế OT, Lương phép, Chuyên cần
            taxable_income = deductions['taxable_income'] - exempt_ot_amount
            # Tính lại thuế TNCN dựa trên TNCT đã trừ các khoản miễn thuế
            deductions = payroll_logic.calculate_deductions(rec, base_income_for_tax - exempt_ot_amount, meal_allowance)
            
            # 5. Lương trong mục tiêu trừ đi các khoản thưởng thực tế
            internal_salary_minus_bonus = max(0, rec.payroll_internal_salary - annual_bonus)
            
            # 6. Thực lĩnh cuối cùng (bao gồm cả các khoản bù KPI/Tiền mặt)
            net_salary_final = total_actual_income + max(0, rec.payroll_kpi_amount) + max(0, rec.payroll_cash_amount)
            
            # Gợi ý xử lý dữ liệu bất thường (Dựa trên TLN mới)
            
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
                    
                    # === XÁC ĐỊNH BIÊN NGÀY CÔNG ===
                    first_boundary = 0
                    last_boundary = 0
                    for d_idx in range(1, 32):
                        if getattr(rec, f'day_{d_idx:02d}', False):
                            if first_boundary == 0: first_boundary = d_idx
                            last_boundary = d_idx

                    # Đếm số lượng thực tế có thể bớt (loại trừ biên và ĐC)
                    protected_for_red = {first_boundary, last_boundary}
                    # Bảo vệ ĐC
                    for d_idx in range(1, 32):
                        att = getattr(rec, f'day_{d_idx:02d}', False)
                        if att and att.code == 'ĐC':
                            protected_for_red.add(d_idx)
                            if d_idx > 1: protected_for_red.add(d_idx - 1)
                            if d_idx < 31: protected_for_red.add(d_idx + 1)

                    can_reduce_n = len([d_idx for d_idx in range(1, 32) if d_idx not in protected_for_red and getattr(rec, f'day_{d_idx:02d}', False) and getattr(rec, f'day_{d_idx:02d}').code == 'N'])
                    can_reduce_ot = len([d_idx for d_idx in range(1, 32) if d_idx not in protected_for_red and getattr(rec, f'ot_day_{d_idx:02d}', False) and getattr(rec, f'ot_day_{d_idx:02d}').code == '0.5N'])
                    
                    # Đếm số lượng thực tế có thể thêm (trong biên)
                    can_add_n = 0
                    can_add_ot = 0
                    if first_boundary and last_boundary:
                        for d_idx in range(first_boundary, last_boundary + 1):
                            if d_idx in protected_for_red: continue # Vẫn tránh ĐC
                            if not getattr(rec, f'day_{d_idx:02d}', False):
                                try:
                                    if datetime.date(year, month, d_idx).weekday() < 6: can_add_n += 1
                                except ValueError: pass
                            elif getattr(rec, f'day_{d_idx:02d}').code == 'N' and not getattr(rec, f'ot_day_{d_idx:02d}', False):
                                can_add_ot += 1

                    mk_gap = (rec.payroll_internal_salary - annual_bonus) - net_salary_base
                    
                    if diff > -buffer or mk_gap < -1:
                        # TRƯỜNG HỢP 1: TLN quá cao hoặc KPI âm -> Cần GIẢM công
                        target_tln = (rec.payroll_internal_salary - annual_bonus) / 1.04
                        amount_to_reduce = max(0, net_salary_base - target_tln)
                        
                        c_05n_red = math.ceil(amount_to_reduce / v_05n) if v_05n > 0 else 0
                        c_n_red = math.ceil(amount_to_reduce / v_n_full) if v_n_full > 0 else 0
                        
                        # Giới hạn gợi ý theo thực tế có thể xóa
                        c_05n_red = min(c_05n_red, can_reduce_ot)
                        c_n_red = min(c_n_red, can_reduce_n)

                        if diff > 0:
                            header = f"<div style='color: #d9534f; font-weight: bold;'>🔻 Thực lĩnh ngoài VƯỢT LNB. Cần GIẢM công:</div>"
                        elif mk_gap < 0:
                            header = f"<div style='color: #d9534f; font-weight: bold;'>🔻 Tiền KPI ĐANG ÂM. Cần GIẢM công</div>"
                        else:
                            header = f"<div style='color: #f0ad4e; font-weight: bold;'>🔸 Tiền KPI đang thấp. Nên GIẢM công để tăng tiền KPI:</div>"

                        anomaly_suggestion = header + f"<ul style='margin-bottom: 0; padding-left: 20px; color: #333;'>"
                        if c_05n_red > 0:
                            anomaly_suggestion += f"<li>Gợi ý: Giảm <b>{c_05n_red}</b> lần <b>0.5N</b></li>"
                        if c_n_red > 0:
                            anomaly_suggestion += f"<li>Hoặc: Giảm <b>{c_n_red}</b> ngày <b>N</b></li>"
                        if c_05n_red <= 0 and c_n_red <= 0:
                            anomaly_suggestion += f"<li><i>Không còn công để giảm (đã chạm biên {first_boundary}->{last_boundary})</i></li>"
                        anomaly_suggestion += "</ul>"

                    elif 0 < rec.payroll_cash_amount < 1000000:
                        # TRƯỜNG HỢP 2: Tiền mặt lẻ (< 1M) -> Cần TĂNG công để bù Gap bằng KPI
                        emp_max_kpi = 70.0
                        if rec.dl_tax_base_salary < 4500000: emp_max_kpi = 55.0
                        elif rec.dl_tax_base_salary < 5000000: emp_max_kpi = 60.0
                        
                        max_mk = net_salary_base * (emp_max_kpi - 50.0) / 50.0
                        amount_to_add = mk_gap - max_mk
                        
                        if amount_to_add > 0:
                            c_05n_add = math.ceil(amount_to_add / v_05n) if v_05n > 0 else 0
                            c_n_add = math.ceil(amount_to_add / v_n_full) if v_n_full > 0 else 0
                            
                            # Giới hạn gợi ý theo thực tế có thể thêm
                            c_05n_add = min(c_05n_add, can_add_ot)
                            c_n_add = min(c_n_add, can_add_n)

                            header = f"<div style='color: #f0ad4e; font-weight: bold;'>🔻 Tiền mặt đang lẻ ({rec.payroll_cash_amount:,.0f} ₫). Cần TĂNG công:</div>"
                            anomaly_suggestion = header + f"<ul style='margin-bottom: 0; padding-left: 20px; color: #333;'>"
                            if c_05n_add > 0:
                                anomaly_suggestion += f"<li>Gợi ý: Tăng <b>{c_05n_add}</b> lần <b>0.5N</b></li>"
                            if c_n_add > 0:
                                anomaly_suggestion += f"<li>Hoặc: Tăng <b>{c_n_add}</b> ngày <b>N</b></li>"
                            if c_05n_add <= 0 and c_n_add <= 0:
                                anomaly_suggestion += f"<li><i>Không còn chỗ trống trong biên ({first_boundary}->{last_boundary}) để thêm</i></li>"
                            anomaly_suggestion += "</ul>"

            hourly_rate = rec.dl_tax_base_salary / 208.0 if rec.dl_tax_base_salary else 0.0
            
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
                'payroll_wage_day': wages['wage_day'] + wages['wage_leave'] + wages.get('wage_bonus_p', 0.0),
                'payroll_wage_day_exp': f"({wages['count_day']/8.0:g} công N + {wages['count_leave']/8.0:g} công P/PL + {wages['count_bonus_p']/8.0:g} công CC) x {hourly_rate:,.0f} x 8h",
                
                'payroll_wage_day_150': wages['wage_day_150'],
                'payroll_wage_day_150_exp': f"{wages['count_day_150']:g}h x {hourly_rate:,.0f} x 150%",
                
                'payroll_wage_night_130': wages['wage_night_130'],
                'payroll_wage_night_130_exp': f"{wages['count_night_130']:g}h x {hourly_rate:,.0f} x 130%",
                
                'payroll_wage_night_200': wages['wage_night_200'],
                'payroll_wage_night_200_exp': f"{wages['count_night_200']:g}h x {hourly_rate:,.0f} x 200%",
                
                'payroll_wage_night_210': wages['wage_night_210'],
                'payroll_wage_night_210_exp': f"{wages['count_night_210']:g}h x {hourly_rate:,.0f} x 210%",
                
                'payroll_wage_night_sun_270': wages['wage_night_sun_270'],
                'payroll_wage_night_sun_270_exp': f"{wages['count_night_sun_270']:g}h x {hourly_rate:,.0f} x 270%",
                
                'payroll_wage_day_sun_200': wages['wage_day_sun_200'],
                'payroll_wage_day_sun_200_exp': f"{wages['count_day_sun_200']:g}h x {hourly_rate:,.0f} x 200%",
                
                'payroll_wage_day_holiday_300': wages['wage_day_holiday_300'],
                'payroll_wage_day_holiday_300_exp': f"{wages['count_day_holiday_300']:g}h x {hourly_rate:,.0f} x 300%",
                
                'payroll_wage_night_holiday_390': wages['wage_night_holiday_390'],
                'payroll_wage_night_holiday_390_exp': f"{wages['count_night_holiday_390']:g}h x {hourly_rate:,.0f} x 390%",
                
                'payroll_revenue_bonus_exp': f"{rev_bonus_base:,.0f} x {rec.total_n + rec.total_d:g}/26 công",
                'payroll_productivity_bonus_exp': f"{prod_bonus_base:,.0f} x {rec.total_n + rec.total_d:g}/26 công",
                'payroll_meal_allowance_exp': f"{rec.month_id.dl_meal_allowance or 0:,.0f} x {rec.total_n + rec.total_d:g}/26 công",
                'payroll_women_allowance_exp': f"{rec.month_id.dl_women_allowance or 0:,.0f} x {rec.total_n + rec.total_d:g}/26 công" if rec.employee_id.sex == 'female' else "",
                
                'payroll_total_wage': total_detailed_wage + revenue_bonus + productivity_bonus,
                'payroll_total_actual_income': total_actual_income,
                'payroll_income_explanation': self._get_income_explanation(
                    gross_lk, deductions['total_deduction'], net_salary_base,
                    meal_allowance, women_allowance, rec.payroll_kpi_amount, total_actual_income
                ),
                'payroll_pit_taxable_explanation': self._get_taxable_explanation(
                    total_detailed_wage, revenue_bonus, productivity_bonus, annual_bonus,
                    women_allowance, meal_allowance, exempt_ot_amount, rec.payroll_kpi_amount
                ),
                
                # Cập nhật các khoản trừ & Thuế TNCN (Ép kiểu số nguyên)
                'payroll_deduction_bhxh': int(round(deductions['bhxh'], 0)),
                'payroll_deduction_bhyt': int(round(deductions['bhyt'], 0)),
                'payroll_deduction_bhtn': int(round(deductions['bhtn'], 0)),
                'payroll_deduction_tncn': int(round(deductions['tncn'], 0)),
                'payroll_total_insurance_deduction': int(round(deductions['total_insurance'], 0)),
                'payroll_pit_taxable_income': int(round(deductions['taxable_income'], 0)),
                'payroll_pit_number_of_dependents': deductions['num_dependents'],
                'payroll_pit_total_deductions': int(round(deductions['total_pit_deductions'], 0)),
                'payroll_pit_assessable_income': int(round(deductions['assessable_income'], 0)),
                'payroll_total_deduction': int(round(deductions['total_deduction'], 0)),
                'payroll_real_net_income': int((total_actual_income - deductions['total_deduction']) // 1000) * 1000,
                'payroll_net_salary_base': int(round(net_salary_base, 0)),
                'payroll_internal_salary_minus_bonus': int(round(internal_salary_minus_bonus, 0)),
            })
                
            # Cập nhật các trường Tiền chuyển khoản: TLN + KPI + Thưởng năm (Theo yêu cầu mới)
            # Đảm bảo transfer_val là số nguyên trước khi tính toán làm tròn
            if rec.payroll_internal_salary == 0 or (rec.month_id.x_has_imported_internal_salary and not rec.month_id.x_is_recalculated):
                transfer_val = 0
                rounded_transfer = 0
                cash_val = 0
                rounded_cash = 0
                kpi_val = 0
                rounded_kpi = 0
                net_salary_final = 0
            else:
                transfer_val = int(round(net_salary_base + (rec.payroll_kpi_amount or 0) + annual_bonus, 0))
                rounded_transfer = int(transfer_val // 1000) * 1000
                
                # Tiền mặt = Lương Nội Bộ - Tiền chuyển khoản đã làm tròn (Để khớp tuyệt đối LNB)
                cash_val = max(0, int(rec.payroll_internal_salary - rounded_transfer))
                rounded_cash = int(cash_val // 1000) * 1000
    
                # Làm tròn Tiền KPI
                kpi_val = int(round(rec.payroll_kpi_amount or 0, 0))
                rounded_kpi = int(kpi_val // 1000) * 1000
    
                # Thực lĩnh cuối cùng = Tổng các khoản thực tế chi trả (Đã làm tròn)
                net_salary_final = rounded_transfer + rounded_cash

            rec.update({
                'payroll_bank_transfer_amount': transfer_val,
                'payroll_bank_transfer_amount_rounded': rounded_transfer,
                'payroll_bank_transfer_amount_rounding_error': int(transfer_val - rounded_transfer),
                'payroll_cash_amount_rounded': rounded_cash,
                'payroll_cash_amount_rounding_error': int(cash_val - rounded_cash),
                'payroll_kpi_amount_rounded': rounded_kpi,
                'payroll_kpi_amount_rounding_error': int(kpi_val - rounded_kpi),
                'payroll_net_salary': net_salary_final,
            })

    def _get_income_explanation(self, gross_lk, deduction, lk, meal, women, kpi, total):
        """Hàm hỗ trợ tạo chuỗi diễn giải chi tiết bằng HTML cho Logic mới (Lk = Gross)"""
        def fmt(val):
            v = int(round(val or 0, 0))
            return "{:,.0f}".format(v).replace(",", ".")
            
        html = f"""
        <div style='font-family: sans-serif; line-height: 1.6;'>
            <div style='margin-bottom: 8px;'>
                <b>1. Tính Thực lĩnh ngoài (Lk):</b><br/>
                &nbsp;&nbsp;&nbsp;&nbsp;{fmt(gross_lk)} (Tổng lương & Thưởng hiệu quả)<br/>
                &nbsp;&nbsp;= <span style='color: #2e7d32; font-weight: bold;'>{fmt(lk)}</span> (Lk - Không khấu trừ)
            </div>
            <div>
                <b>2. Tính Tổng thu nhập thực tế:</b><br/>
                &nbsp;&nbsp;+ {fmt(kpi)} (Tiền KPI)<br/>
                &nbsp;&nbsp;= <span style='color: #007bff; font-weight: bold;'>{fmt(total)}</span> (Tổng TN Thực tế)
            </div>
            <div>
                <b>3. Thực lĩnh thực tế (Sau khấu trừ):</b><br/>
                &nbsp;&nbsp;&nbsp;&nbsp;{fmt(total)} (Tổng TN Thực tế)<br/>
                &nbsp;&nbsp;- {fmt(deduction)} (Tổng các khoản trừ: BH + Thuế)<br/>
                &nbsp;&nbsp;= <span style='color: #d32f2f; font-weight: bold; font-size: 1.1em;'>{fmt(int((total - deduction) // 1000) * 1000)}</span> (Thực lĩnh thực tế - Đã làm tròn xuống hàng nghìn)
            </div>
        </div>
        """
        return html

    def _get_taxable_explanation(self, wage, rev, prod, annual, women, meal, exempt_ot, kpi):
        """Hàm tạo chuỗi giải thích Thu nhập chịu thuế (TNCT)"""
        def fmt(val):
            v = int(round(val or 0, 0))
            return "{:,.0f}".format(v).replace(",", ".")
            
        gross = wage + rev + prod + annual + women + meal + (kpi or 0.0)
        taxable = gross - meal - exempt_ot
        
        parts = []
        if wage: parts.append(f"{fmt(wage)} (Lương)")
        if rev: parts.append(f"{fmt(rev)} (T.DT)")
        if prod: parts.append(f"{fmt(prod)} (T.NS)")
        if annual: parts.append(f"{fmt(annual)} (T.Năm)")
        if women: parts.append(f"{fmt(women)} (P.Nữ)")
        if meal: parts.append(f"{fmt(meal)} (Ăn ca)")
        if kpi: parts.append(f"{fmt(kpi)} (KPI)")
        
        formula = " + ".join(parts)
        
        html = (
            f"<div style='font-size: 0.9em; color: #555;'>"
            f"<div>&#8226; Tổng thu nhập gộp: {formula} = <b>{fmt(gross)}</b></div>"
            f"<div style='margin-top: 3px;'>&#8226; Thu nhập chịu thuế: {fmt(gross)} (Gộp) - {fmt(meal)} (Ăn ca) - <span style='color: #d9534f;'>{fmt(exempt_ot)} (Miễn thuế OT & Phép)</span> = <b style='color: #28a745;'>{fmt(taxable)}</b></div>"
            f"<div style='font-size: 0.85em; font-style: italic; color: #777; margin-top: 2px;'>* Toàn bộ thu nhập từ tăng ca, làm đêm, lương nghỉ phép và thưởng chuyên cần được miễn thuế.</div>"
            f"</div>"
        )
        return html

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
    def _check_holiday_attendance_pl(self):
        """
        Ràng buộc: Nếu chấm công làm thêm là 1LN hoặc 0.5LN (Lễ)
        thì công thường của ngày đó bắt buộc phải là PL (Phép Lễ).
        """
        for rec in self:
            for i in range(1, 32):
                ot_att = getattr(rec, f'ot_day_{i:02d}')
                if ot_att and ot_att.code in ['1LN', '0.5LN']:
                    norm_att = getattr(rec, f'day_{i:02d}')
                    if not norm_att or norm_att.code != 'PL':
                        raise ValidationError(_(
                            "Nhân viên %s: Ngày %02d có công làm thêm là %s (Lễ). "
                            "Yêu cầu công thường của ngày này phải là PL (Phép Lễ) để đảm bảo đúng chế độ."
                        ) % (rec.employee_id.name, i, ot_att.code))

    # @api.constrains('day_01', 'day_02', 'day_03', 'day_04', 'day_05', 'day_06', 'day_07', 'day_08', 'day_09', 'day_10',
    #                 'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20',
    #                 'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31',
    #                 'ot_day_01', 'ot_day_02', 'ot_day_03', 'ot_day_04', 'ot_day_05', 'ot_day_06', 'ot_day_07', 'ot_day_08', 'ot_day_09', 'ot_day_10',
    #                 'ot_day_11', 'ot_day_12', 'ot_day_13', 'ot_day_14', 'ot_day_15', 'ot_day_16', 'ot_day_17', 'ot_day_18', 'ot_day_19', 'ot_day_20',
    #                 'ot_day_21', 'ot_day_22', 'ot_day_23', 'ot_day_24', 'ot_day_25', 'ot_day_26', 'ot_day_27', 'ot_day_28', 'ot_day_29', 'ot_day_30', 'ot_day_31')
    # def _check_departure_date_attendance(self):
    #     from . import attendance_logic
    #     for rec in self:
    #         vals_to_clear = attendance_logic.check_departure_date_violation(rec)
    #         if vals_to_clear:
    #             rec.sudo().write(vals_to_clear)

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
            'size': 'xl',
            'context': {
                'default_line_id': self.id,
                'default_employee_name': self.employee_name,
                'default_identification_id': self.identification_id,
                'default_current_lk': self.payroll_net_salary_base,
                'default_target_salary': self.payroll_internal_salary,
            }
        }

    def action_open_lnb_wizard(self):
        """Mở Wizard Sửa nhanh Lương Nội Bộ (LNB)."""
        self.ensure_one()
        return {
            'name': f'Sửa nhanh LNB - {self.employee_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'dl.salary.kpi.lnb.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_line_id': self.id,
                'default_new_lnb': self.payroll_internal_salary,
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
    #                 "Lý do: Thực lĩnh ngoài(TLN) hoặc KPI (Mk) quá cao. \n"
    #                 "Giải pháp: Hãy dùng nút 'Sửa nhanh' để giảm bớt ngày công hoặc giảm điểm KPI."
    #             ) % (rec.employee_name, fmt(rec.payroll_bank_transfer_amount), fmt(rec.payroll_internal_salary), fmt(diff)))

    @api.depends('payroll_bank_transfer_amount', 'dl_tax_base_salary')
    def _compute_payroll_tracking_percentage(self):
        for rec in self:
            if rec.payroll_bank_transfer_amount:
                # Công thức yêu cầu: (Lương CB Thuế / Tiền CK) * 100
                # Vì Odoo dùng widget="percentage" (tự nhân 100 khi hiển thị), 
                # nên giá trị lưu trữ trong database phải là số thập phân (A/B).
                # Ví dụ: 0.5 sẽ hiển thị là 50.00%
                percentage_value = (rec.dl_tax_base_salary / rec.payroll_bank_transfer_amount) * 100
                rec.payroll_tracking_percentage = round(percentage_value / 100.0, 4)
            else:
                rec.payroll_tracking_percentage = 0.0

    # --- LOGIC PHÉP THUẬT WING (CHUYỂN TỪ WIZARD SANG) ---
    def _get_work_boundaries(self):
        """Trả về (first_day, last_day) là index của ngày có công đầu tiên và cuối cùng."""
        first_day = 0
        last_day = 0
        for i in range(1, 32):
            if getattr(self, f'day_{i:02d}', False):
                if first_day == 0:
                    first_day = i
                last_day = i
        return first_day, last_day

    def _get_protected_days(self, check_boundaries=True):
        """Lấy danh sách các ngày không được phép XÓA công."""
        from calendar import monthrange
        protected = set()
        month_date = self.month_id.date_month
        last_day_in_month = monthrange(month_date.year, month_date.month)[1]

        # 1. Bảo vệ các ngày quanh ĐC (Đổi công)
        for i in range(1, last_day_in_month + 1):
            att = getattr(self, f'day_{i:02d}')
            if att and getattr(att, 'code', False) == 'ĐC':
                protected.add(i)
                if i > 1: protected.add(i - 1)
                if i < last_day_in_month: protected.add(i + 1)
        
        # 2. Bảo vệ ngày đầu tiên và cuối cùng đi làm
        if check_boundaries:
            first, last = self._get_work_boundaries()
            if first: protected.add(first)
            if last: protected.add(last)
        return protected

    def action_run_wing_magic_logic(self):
        """
        Logic cốt lõi của Phép thuật Wing: Tự động thêm/bớt công để khớp Ln.
        """
        import random
        import datetime
        from odoo.exceptions import UserError
        
        for rec in self:
            protected = rec._get_protected_days(check_boundaries=True)
            company_id = rec.company_id.id
            
            # Load types
            att_type_n = self.env['dl.salary.kpi.attendance.type'].search([('code', '=', 'N'), ('company_id', '=', company_id)], limit=1)
            att_type_05n = self.env['dl.salary.kpi.attendance.type'].search([('code', '=', '0.5N'), ('company_id', '=', company_id)], limit=1)

            def update_and_get_state():
                rec.action_generate_kpi_scores(max_allowed=70)
                return rec.payroll_kpi_amount, rec.payroll_cash_amount

            # VÒNG LẶP 1: Xử lý KPI âm -> Cắt công
            kpi, cash = update_and_get_state()
            iterations = 0
            while kpi < -100 and iterations < 30:
                iterations += 1
                ot_days = [i for i in range(1, 32) if i not in protected and getattr(rec, f'ot_day_{i:02d}')]
                if ot_days:
                    d = random.choice(ot_days)
                    rec.write({f'ot_day_{d:02d}': False})
                else:
                    main_days = [i for i in range(1, 32) if i not in protected and getattr(rec, f'day_{i:02d}') and getattr(rec, f'day_{i:02d}').code in ('N', 'Đ')]
                    if main_days:
                        d = random.choice(main_days)
                        rec.write({f'day_{d:02d}': False, f'ot_day_{d:02d}': False})
                    else:
                        break
                kpi, cash = update_and_get_state()

            # VÒNG LẶP 2: Tối ưu tiền mặt -> Thêm công
            kpi, cash = update_and_get_state()
            iterations = 0
            first_b, last_b = rec._get_work_boundaries()
            while cash > 1000 and iterations < 30:
                iterations += 1
                can_add_ot = [i for i in range(1, 32) if i not in protected and first_b <= i <= last_b 
                              and getattr(rec, f'day_{i:02d}') and getattr(rec, f'day_{i:02d}').code == 'N' 
                              and not getattr(rec, f'ot_day_{i:02d}')]
                if can_add_ot:
                    d = random.choice(can_add_ot)
                    rec.write({f'ot_day_{d:02d}': att_type_05n.id})
                else:
                    year, month = rec.month_id.date_month.year, rec.month_id.date_month.month
                    can_add_n = []
                    for i in range(first_b, last_b + 1):
                        if i in protected or getattr(rec, f'day_{i:02d}'): continue
                        try:
                            if datetime.date(year, month, i).weekday() < 6:
                                can_add_n.append(i)
                        except: pass
                    
                    if can_add_n and (rec.total_n + rec.total_d < 27):
                        d = random.choice(can_add_n)
                        rec.write({f'day_{d:02d}': att_type_n.id})
                    else:
                        break
                kpi, cash = update_and_get_state()
                if kpi > (rec.payroll_internal_salary * 0.4): break
        return True

    def action_wing_magic_anomaly_fix(self):
        """
        Phương thức cho nút 'Tự Động' tại Tab 6: Unify logic.
        """
        for rec in self:
            # 1. Logic xóa sạch nếu Ln = 0
            if rec.payroll_internal_salary == 0 and rec.payroll_net_salary_base > 0:
                vals = {'payroll_kpi_score': 0, 'payroll_kpi_amount': 0, 'payroll_cash_amount': 0, 'x_is_anomaly_resolved': True}
                for i in range(1, 32):
                    vals[f'day_{i:02d}'] = False
                    vals[f'ot_day_{i:02d}'] = False
                rec.write(vals)
                # Tính toán lại ngay lập tức để cập nhật số lượng công và tiền thực lĩnh
                rec._compute_totals()
                rec._compute_payroll_internal()
            else:
                # 2. Logic Wing Magic (Tự cân đối công)
                rec.action_run_wing_magic_logic()
        
        return True
