# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date

from odoo.models import Constraint

class SalaryKpiBonusYear(models.Model):
    _name = 'dl.salary.kpi.bonus.year'
    _description = 'Cấu hình thưởng trong năm'
    _order = 'year desc'

    year = fields.Integer(string='Năm', required=True, default=lambda self: date.today().year)
    name = fields.Char(string='Tên cấu hình', compute='_compute_name', store=True)
    line_ids = fields.One2many('dl.salary.kpi.bonus.line', 'year_id', string='Chi tiết thưởng')
    active = fields.Boolean(string='Đang hoạt động', default=True)
    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company)

    _year_unique = Constraint('unique(year, company_id)', 'Cấu hình cho năm này của công ty đã tồn tại!')

    @api.depends('year')
    def _compute_name(self):
        for rec in self:
            rec.name = f"Cấu hình thưởng năm {rec.year}"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('line_ids'):
                year = vals.get('year', date.today().year)
                # Tạo dữ liệu mặc định
                default_lines = [
                    (0, 0, {
                        'date': date(year, 3, 8),
                        'name': 'Thưởng 08/03',
                        'amount': 500000,
                        'gender': 'female',
                    }),
                    (0, 0, {
                        'date': date(year, 4, 30),
                        'name': 'Thưởng 30/04',
                        'amount': 500000,
                        'gender': 'all',
                    }),
                    (0, 0, {
                        'date': date(year, 9, 2),
                        'name': 'Thưởng 02/09',
                        'amount': 500000,
                        'gender': 'all',
                    }),
                    (0, 0, {
                        'date': date(year, 1, 1),
                        'name': 'Thưởng Tết Dương Lịch',
                        'amount': 500000,
                        'gender': 'all',
                    }),
                ]
                vals['line_ids'] = default_lines
        return super().create(vals_list)

class SalaryKpiBonusLine(models.Model):
    _name = 'dl.salary.kpi.bonus.line'
    _description = 'Chi tiết thưởng'

    year_id = fields.Many2one('dl.salary.kpi.bonus.year', string='Năm cấu hình', ondelete='cascade')
    date = fields.Date(string='Ngày thưởng', required=True)
    name = fields.Char(string='Tên khoản thưởng', required=True)
    amount = fields.Monetary(string='Số tiền thưởng', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', related='year_id.company_id.currency_id')
    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('all', 'Tất cả')
    ], string='Giới tính áp dụng', default='all', required=True)
    active = fields.Boolean(string='Hoạt động', default=True)
