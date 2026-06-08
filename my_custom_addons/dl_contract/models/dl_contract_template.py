# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


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

    def action_preview_template(self):
        """Mở tab mới để xem trước file template dưới dạng PDF.
        
        Controller sẽ dùng LibreOffice để chuyển đổi .docx → .pdf.
        Nếu LibreOffice không có, file .docx sẽ được tải xuống thay thế.
        """
        self.ensure_one()
        if not self.template_file:
            raise UserError(_("Template chưa có file đính kèm. Vui lòng upload file .docx trước!"))

        preview_url = f'/dl_contract/preview_template/{self.id}'
        return {
            'type': 'ir.actions.act_url',
            'url': preview_url,
            'target': 'new',  # Mở trong tab mới
        }
