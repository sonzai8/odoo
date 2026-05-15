# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.models import Constraint

class SalaryKpiAttendanceType(models.Model):
    """
    Model quản lý các loại hình chấm công cho KPI và lương.
    """
    _name = 'dl.salary.kpi.attendance.type'
    _description = 'Loại công KPI'
    _rec_name = 'code'
    _order = 'sequence, id'

    code = fields.Char(string='Mã ký hiệu', required=True, help="VD: N, D, P, K")
    name = fields.Char(string='Tên loại công', required=True)
    note = fields.Text(string='Ghi chú')
    weight = fields.Float(string='Trọng số công', default=1.0, help="Giá trị quy đổi công (1.0, 0.5, 0.0...)", digits=(6,4))
    sequence = fields.Integer(string='Thứ tự', default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company)
    apply_to = fields.Selection([
        ('normal', 'Chỉ Công Thường'),
        ('overtime', 'Chỉ Làm Thêm'),
        ('both', 'Cả Hai')
    ], string='Phạm vi áp dụng', default='both', required=True)
    ot_type = fields.Selection([
        ('day', 'Tăng ca Ngày'),
        ('night', 'Tăng ca Đêm'),
        ('none', 'Không phải tăng ca')
    ], string='Loại tăng ca', default='none')

    _code_company_unique = models.Constraint(
        'unique(code, company_id)',
        'Mã loại công này đã tồn tại trong công ty này!'
    )

    @api.onchange('code')
    def _onchange_code(self):
        if self.code:
            self.code = self.code.upper()
