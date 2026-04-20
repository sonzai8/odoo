# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SalaryKpiCalc(models.Model):
    _name = 'dl.salary.kpi.calc'
    _description = 'Bảng tính KPI'
    _order = 'id desc'

    month_id = fields.Many2one('dl.salary.kpi.month', string='Tháng cân đối', required=True)
    name = fields.Char(string='Tên bảng tính', compute='_compute_name', store=True)
    line_ids = fields.One2many('dl.salary.kpi.calc.line', 'calc_id', string='Chi tiết KPI')
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('confirmed', 'Xác nhận')
    ], string='Trạng thái', default='draft')
    
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)

    @api.depends('month_id')
    def _compute_name(self):
        for rec in self:
            if rec.month_id:
                rec.name = f"Bảng tính KPI - {rec.month_id.name}"
            else:
                rec.name = "Bảng tính mới"

    def action_load_employees(self):
        self.ensure_one()
        if not self.month_id:
            return
        
        # Load from Month lines
        month_lines = self.month_id.line_ids.filtered(lambda l: not l.is_disabled)
        line_vals = []
        for ml in month_lines:
            line_vals.append((0, 0, {
                'employee_id': ml.employee_id.id,
                'employee_name': ml.employee_name,
                'identification_id': ml.identification_id,
                'job_title': ml.employee_id.job_title if ml.employee_id else '',
            }))
        
        self.line_ids.unlink()
        self.write({'line_ids': line_vals})

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_export_excel(self):
        # Placeholder for later
        return True

    def action_import_excel(self):
        # Placeholder for later
        return True

class SalaryKpiCalcLine(models.Model):
    _name = 'dl.salary.kpi.calc.line'
    _description = 'Chi tiết tính KPI'
    _order = 'id'

    calc_id = fields.Many2one('dl.salary.kpi.calc', string='Bảng tính', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Nhân viên')
    employee_name = fields.Char(string='Họ Và Tên')
    identification_id = fields.Char(string='MST/CCCD')
    job_title = fields.Char(string='Chức vụ')
    
    currency_id = fields.Many2one(related='calc_id.currency_id', readonly=True)
    salary_base = fields.Monetary(string='Lương tính KPI', currency_field='currency_id')
    kpi_amount = fields.Monetary(string='KPI', currency_field='currency_id')
    payout_ratio = fields.Float(string='Tỷ lệ % hưởng lương')
    kpi_coefficient = fields.Float(string='Hệ số KPI', default=1.0)
    kpi_score = fields.Float(string='Điểm KPI', default=100.0)
    notes = fields.Text(string='Ghi chú')
