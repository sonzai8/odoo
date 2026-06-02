# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class DlPublicHoliday(models.Model):
    _name = 'dl.public.holiday'
    _description = 'Ngày nghỉ lễ chung'
    _order = 'date_from desc'

    def _get_years(self):
        return [(str(y), str(y)) for y in range(2024, 2050)]

    name = fields.Char(string='Tên ngày lễ', required=True)
    date_from = fields.Date(string='Từ ngày', required=True)
    date_to = fields.Date(string='Đến ngày', required=True)
    year = fields.Selection(selection='_get_years', string='Năm', compute='_compute_year', store=True)
    note = fields.Text(string='Ghi chú')
    active = fields.Boolean(string='Kích hoạt', default=True)
    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company)

    @api.depends('date_from')
    def _compute_year(self):
        for record in self:
            if record.date_from:
                record.year = str(record.date_from.year)
            else:
                record.year = False

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from and record.date_to and record.date_from > record.date_to:
                raise ValidationError(_('Ngày bắt đầu không được lớn hơn ngày kết thúc!'))

    @api.model
    def get_holiday_dates(self, start_date, end_date=None, company_id=None):
        """
        Lấy danh sách các ngày thực sự là ngày lễ trong một khoảng thời gian.
        Trả về một tập hợp (set) các ngày (datetime.date).
        """
        if not company_id:
            company_id = self.env.company.id

        domain = [
            ('company_id', '=', company_id),
            ('active', '=', True)
        ]

        if end_date:
            domain += [
                '|',
                '&', ('date_from', '<=', end_date), ('date_to', '>=', start_date),
                '&', ('date_from', '<=', end_date), ('date_to', '=', False) # Xử lý trường hợp chỉ có ngày bắt đầu
            ]
        else:
            domain += [('date_to', '>=', start_date)]

        holidays = self.search(domain)
        holiday_dates = set()
        
        for h in holidays:
            d = h.date_from
            end = h.date_to or h.date_from
            while d <= end:
                if not end_date or d <= end_date:
                    holiday_dates.add(d)
                d += timedelta(days=1)
                
        return holiday_dates
