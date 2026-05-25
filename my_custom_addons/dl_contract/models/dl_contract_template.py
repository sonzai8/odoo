# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DlContractTemplate(models.Model):
    _name = 'dl.contract.template'
    _description = 'Template hợp đồng Word'

    name = fields.Char(string='Tên template', required=True)
    contract_type_id = fields.Many2one('dl.contract.type', string='Loại hợp đồng áp dụng', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    template_file = fields.Binary(string='File mẫu (.docx)', required=True, attachment=True)
    template_filename = fields.Char(string='Tên file mẫu')
    active = fields.Boolean(default=True, string='Đang sử dụng')
    description = fields.Text(string='Mô tả')
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company, index=True)
