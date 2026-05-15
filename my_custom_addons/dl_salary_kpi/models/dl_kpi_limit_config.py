# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class DlKpiLimitConfig(models.Model):
    _name = 'dl.salary.kpi.limit.config'
    _description = 'Cấu hình Giới hạn Điểm KPI'
    _order = 'id desc'

    name = fields.Char(string='Tên cấu hình', required=True)
    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', related='company_id.currency_id')
    
    is_applied = fields.Boolean(string='Đang áp dụng', default=False, help="Chỉ có 1 cấu hình được áp dụng tại một thời điểm cho mỗi công ty")
    date_start = fields.Date(string='Ngày bắt đầu áp dụng', default=fields.Date.context_today)

    line_ids = fields.One2many('dl.salary.kpi.limit.line', 'config_id', string='Các ngưỡng giới hạn')

    @api.constrains('is_applied', 'company_id')
    def _check_unique_applied_config(self):
        for rec in self:
            if rec.is_applied:
                other_applied = self.search([
                    ('id', '!=', rec.id),
                    ('company_id', '=', rec.company_id.id),
                    ('is_applied', '=', True)
                ])
                if other_applied:
                    other_applied.write({'is_applied': False})

    def action_init_defaults(self):
        """Khởi tạo các mốc giới hạn mặc định theo chuẩn Đức Lâm"""
        for rec in self:
            if rec.line_ids:
                raise ValidationError(_("Bạn chỉ có thể khởi tạo mẫu khi danh sách ngưỡng còn trống!"))
            
            self.env['dl.salary.kpi.limit.line'].create([
                {
                    'config_id': rec.id,
                    'min_base_salary': 0,
                    'max_base_salary': 4500000,
                    'min_kpi': 50.0,
                    'max_kpi': 55.0,
                    'name': 'Lương cơ bản dưới 4.5 triệu'
                },
                {
                    'config_id': rec.id,
                    'min_base_salary': 4500000,
                    'max_base_salary': 5000000,
                    'min_kpi': 55.0,
                    'max_kpi': 60.0,
                    'name': 'Lương cơ bản từ 4.5 đến 5 triệu'
                },
                {
                    'config_id': rec.id,
                    'min_base_salary': 5000000,
                    'max_base_salary': 0, # Không giới hạn trên
                    'min_kpi': 60.0,
                    'max_kpi': 70.0,
                    'name': 'Lương cơ bản trên 5 triệu'
                },
            ])

class DlKpiLimitLine(models.Model):
    _name = 'dl.salary.kpi.limit.line'
    _description = 'Dòng chi tiết Giới hạn KPI'
    _order = 'min_base_salary asc'

    config_id = fields.Many2one('dl.salary.kpi.limit.config', string='Cấu hình', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Công ty', related='config_id.company_id', store=True)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', related='config_id.currency_id')
    
    name = fields.Char(string='Mô tả mốc', help="Ví dụ: Công nhân sản xuất lương thấp")
    min_base_salary = fields.Monetary(string='Lương cơ bản từ', required=True, currency_field='currency_id')
    max_base_salary = fields.Monetary(string='Lương cơ bản đến', currency_field='currency_id', help='Để trống (0) nếu không có giới hạn trên')
    
    min_kpi = fields.Float(string='Điểm KPI tối thiểu', required=True, default=50.0)
    max_kpi = fields.Float(string='Điểm KPI tối đa', required=True, default=100.0)

    @api.constrains('min_base_salary', 'max_base_salary')
    def _check_salary_range(self):
        for rec in self:
            if rec.max_base_salary and rec.min_base_salary >= rec.max_base_salary:
                raise ValidationError(_("Lương cơ bản đến phải lớn hơn lương cơ bản từ."))

    @api.constrains('min_kpi', 'max_kpi')
    def _check_kpi_range(self):
        for rec in self:
            if rec.min_kpi > rec.max_kpi:
                raise ValidationError(_("Điểm KPI tối đa phải lớn hơn hoặc bằng điểm KPI tối thiểu."))
