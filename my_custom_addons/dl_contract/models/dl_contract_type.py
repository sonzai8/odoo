# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class DlContractType(models.Model):
    _name = 'dl.contract.type'
    _description = 'Loại hợp đồng lao động'
    _order = 'sequence, id'

    name = fields.Char(string='Tên loại hợp đồng', required=True, translate=True)
    code = fields.Char(string='Mã loại', required=True, copy=False)
    duration_type = fields.Selection([
        ('fixed', 'Có thời hạn'),
        ('indefinite', 'Vô thời hạn')
    ], string='Thời hạn', default='fixed', required=True)
    default_duration_months = fields.Integer(string='Thời hạn mặc định (tháng)', default=12)
    description = fields.Text(string='Mô tả chi tiết')
    template_id = fields.Many2one('dl.contract.template', string='Template mặc định', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    active = fields.Boolean(default=True, string='Đang sử dụng')
    sequence = fields.Integer(default=10, string='Thứ tự')
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company, index=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    default_wage = fields.Monetary(string='Lương cơ bản mặc định', currency_field='currency_id')

    _code_company_uniq = models.Constraint(
        'UNIQUE (code, company_id)', 
        'Mã loại hợp đồng phải là duy nhất trong cùng một công ty!'
    )

    def action_preview_template(self):
        """Mở xem trước template mặc định của loại hợp đồng này.
        
        Tái sử dụng controller preview đã có của dl.contract.template.
        """
        self.ensure_one()
        if not self.template_id:
            raise UserError(_("Loại hợp đồng này chưa được gán Template mặc định!"))
        if not self.template_id.template_file:
            raise UserError(_("Template '%s' chưa có file đính kèm. Vui lòng upload file .docx trước!") % self.template_id.name)

        return {
            'type': 'ir.actions.act_url',
            'url': f'/dl_contract/preview_template/{self.template_id.id}',
            'target': 'new',
        }
