# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SalaryKpiAttendanceLine(models.Model):
    _name = 'dl.salary.kpi.attendance.line'
    _description = 'Chi tiết chấm công KPI'
    _order = 'day asc'

    month_line_id = fields.Many2one('dl.salary.kpi.line', string='Dòng lương', ondelete='cascade', required=True)
    day = fields.Integer(string='Ngày', required=True)
    attendance_type_id = fields.Many2one('dl.salary.kpi.attendance.type', string='Loại công')
    
    @api.constrains('day')
    def _check_day(self):
        for rec in self:
            if rec.day < 1 or rec.day > 31:
                raise models.ValidationError(_("Ngày phải nằm trong khoảng 1-31"))
