# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class DlBonusPolicy(models.Model):
    _name = 'dl.salary.kpi.bonus.policy'
    _description = 'Phiên bản Quy chế Thưởng'
    _order = 'id desc'

    name = fields.Char(string='Tên phiên bản (VD: Tháng 5/2026)', required=True)
    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', related='company_id.currency_id')
    
    is_applied = fields.Boolean(string='Đang áp dụng', default=False, help="Chỉ có 1 quy chế được active tại một thời điểm cho mỗi công ty")
    date_start = fields.Date(string='Ngày bắt đầu áp dụng', default=fields.Date.context_today)
    document = fields.Binary(string='Tệp đính kèm (Word/Excel)')
    document_name = fields.Char(string='Tên tệp đính kèm')

    revenue_job_titles = fields.Char(string='Chức vụ hưởng Thưởng Doanh Thu', help='Mã chức vụ cách nhau bằng dấu phẩy. VD: CV,KTT,QL,QĐ,TL,PGĐ,GĐ,NV,KT,TK,CN,LX')

    kpi_range_line_ids = fields.One2many('dl.salary.kpi.range.config', 'policy_id', string='Dải điểm KPI')
    revenue_line_ids = fields.One2many('dl.salary.kpi.revenue.bonus', 'policy_id', string='Mốc Thưởng Doanh Thu')
    productivity_line_ids = fields.One2many('dl.salary.kpi.productivity.bonus', 'policy_id', string='Mốc Thưởng Năng Suất')

    @api.constrains('is_applied', 'company_id')
    def _check_unique_applied_policy(self):
        for rec in self:
            if rec.is_applied:
                # Tìm các policy khác đang applied của cùng công ty và tắt chúng đi
                other_applied = self.search([
                    ('id', '!=', rec.id),
                    ('company_id', '=', rec.company_id.id),
                    ('is_applied', '=', True)
                ])
                if other_applied:
                    other_applied.write({'is_applied': False})
                
                # Sau khi thay đổi policy active, cần báo cho Odoo biết các bản ghi Month liên quan cần tính toán lại
                months = self.env['dl.salary.kpi.month'].search([('company_id', '=', rec.company_id.id)])
                if months:
                    months.modified(['active_policy_id'])

    def action_init_defaults(self):
        """Khởi tạo dữ liệu mẫu cho Quy chế (theo chuẩn Đức Lâm)"""
        for rec in self:
            if rec.revenue_line_ids or rec.productivity_line_ids or rec.kpi_range_line_ids:
                raise ValidationError(_("Bạn chỉ có thể khởi tạo mẫu khi danh sách mốc thưởng còn trống!"))
            
            # Mốc KPI
            self.env['dl.salary.kpi.range.config'].create([
                {'policy_id': rec.id, 'salary_from': 0, 'salary_to': 4500000, 'min_kpi': 50.0, 'max_kpi': 55.0},
                {'policy_id': rec.id, 'salary_from': 4500000, 'salary_to': 5000000, 'min_kpi': 55.0, 'max_kpi': 60.0},
                {'policy_id': rec.id, 'salary_from': 5000000, 'salary_to': 0, 'min_kpi': 60.0, 'max_kpi': 70.0},
            ])

            # Gán mặc định tất cả các chức vụ cho Thưởng Doanh Thu
            if not rec.revenue_job_titles:
                rec.revenue_job_titles = 'CV,KTT,QL,QĐ,TL,PGĐ,GĐ,NV,KT,TK,CN,LX'

            # Mốc Doanh Thu
            self.env['dl.salary.kpi.revenue.bonus'].create([
                {'policy_id': rec.id, 'min_revenue': 0, 'max_revenue': 20000000000, 'bonus_amount': 0},
                {'policy_id': rec.id, 'min_revenue': 20000000000, 'max_revenue': 30000000000, 'bonus_amount': 2000000},
                {'policy_id': rec.id, 'min_revenue': 30000000000, 'max_revenue': 50000000000, 'bonus_amount': 2300000},
                {'policy_id': rec.id, 'min_revenue': 50000000000, 'max_revenue': 70000000000, 'bonus_amount': 3000000},
                {'policy_id': rec.id, 'min_revenue': 70000000000, 'max_revenue': 0, 'bonus_amount': 3500000},
            ])

            # Mốc Năng Suất
            self.env['dl.salary.kpi.productivity.bonus'].create([
                {'policy_id': rec.id, 'name': 'Quản lý cấp cao', 'job_titles': 'CV,KTT,QL,QĐ,TL,PGĐ,GĐ', 'bonus_amount': 2000000},
                {'policy_id': rec.id, 'name': 'Nhân viên gián tiếp', 'job_titles': 'NV,KT,TK', 'bonus_amount': 1500000},
                {'policy_id': rec.id, 'name': 'Nhân viên sản xuất', 'job_titles': 'CN,LX', 'bonus_amount': 1000000},
            ])


class DlKpiRangeConfig(models.Model):
    _name = 'dl.salary.kpi.range.config'
    _description = 'Cấu hình Dải điểm KPI theo Lương'
    _order = 'salary_from asc'

    policy_id = fields.Many2one('dl.salary.kpi.bonus.policy', string='Quy chế', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Công ty', related='policy_id.company_id', store=True)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', related='policy_id.currency_id')
    
    salary_from = fields.Monetary(string='Lương cơ bản từ (VNĐ)', required=True, currency_field='currency_id')
    salary_to = fields.Monetary(string='Lương cơ bản đến (VNĐ)', currency_field='currency_id', help='Để trống (0) nếu không có giới hạn trên')
    min_kpi = fields.Float(string='KPI Tối thiểu', required=True)
    max_kpi = fields.Float(string='KPI Tối đa', required=True)

    @api.constrains('salary_from', 'salary_to', 'min_kpi', 'max_kpi')
    def _check_valid_range(self):
        for rec in self:
            if rec.salary_to and rec.salary_from >= rec.salary_to:
                raise ValidationError(_("Lương cơ bản đến phải lớn hơn Lương cơ bản từ."))
            if rec.min_kpi > rec.max_kpi:
                raise ValidationError(_("Điểm KPI tối đa phải lớn hơn hoặc bằng KPI tối thiểu."))

    def name_get(self):
        result = []
        for rec in self:
            name = f"Từ {rec.salary_from:,.0f} đ"
            if rec.salary_to:
                name += f" dưới {rec.salary_to:,.0f} đ"
            else:
                name += " trở lên"
            name += f" (KPI: {rec.min_kpi} - {rec.max_kpi})"
            result.append((rec.id, name))
        return result

class DlRevenueBonus(models.Model):
    _name = 'dl.salary.kpi.revenue.bonus'
    _description = 'Cấu hình Thưởng Doanh Thu'
    _order = 'min_revenue desc'

    policy_id = fields.Many2one('dl.salary.kpi.bonus.policy', string='Quy chế', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Công ty', related='policy_id.company_id', store=True)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', related='policy_id.currency_id')
    
    min_revenue = fields.Monetary(string='Doanh thu từ (VNĐ)', required=True, currency_field='currency_id')
    max_revenue = fields.Monetary(string='Doanh thu đến (VNĐ)', currency_field='currency_id', help='Để trống (0) nếu không có giới hạn trên')
    bonus_amount = fields.Monetary(string='Mức thưởng (VNĐ)', required=True, currency_field='currency_id')

    @api.constrains('min_revenue', 'max_revenue')
    def _check_revenue_range(self):
        for rec in self:
            if rec.max_revenue and rec.min_revenue >= rec.max_revenue:
                raise ValidationError(_("Doanh thu đến phải lớn hơn Doanh thu từ."))

    def name_get(self):
        result = []
        for rec in self:
            name = f"Từ {rec.min_revenue:,.0f} đ"
            if rec.max_revenue:
                name += f" dưới {rec.max_revenue:,.0f} đ"
            else:
                name += " trở lên"
            name += f" - Thưởng {rec.bonus_amount:,.0f} đ"
            result.append((rec.id, name))
        return result

class DlProductivityBonus(models.Model):
    _name = 'dl.salary.kpi.productivity.bonus'
    _description = 'Cấu hình Thưởng Năng Suất'
    _order = 'bonus_amount desc'

    policy_id = fields.Many2one('dl.salary.kpi.bonus.policy', string='Quy chế', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Công ty', related='policy_id.company_id', store=True)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', related='policy_id.currency_id')
    
    name = fields.Char(string='Tên nhóm chức vụ', required=True, help="Ví dụ: Quản lý cấp cao, Nhân viên gián tiếp")
    job_titles = fields.Char(string='Mã chức vụ áp dụng', required=True, help='Cách nhau bằng dấu phẩy. VD: CV,KTT,QL,QĐ,TL,PGĐ')
    bonus_amount = fields.Monetary(string='Mức thưởng (VNĐ)', required=True, currency_field='currency_id')

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, f"{rec.name} - Thưởng {rec.bonus_amount:,.0f} đ"))
        return result
