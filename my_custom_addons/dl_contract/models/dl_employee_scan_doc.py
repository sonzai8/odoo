# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DlEmployeeScanDoc(models.Model):
    """
    Lưu trữ tài liệu scan (PDF) gắn với từng nhân viên.
    Được sử dụng bởi tính năng 'Số hoá Hợp đồng'.
    """
    _name = 'dl.employee.scan.doc'
    _description = 'Tài liệu Scan Nhân viên'
    _order = 'upload_date desc, id desc'

    name = fields.Char(
        string='Tên tài liệu',
        required=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Nhân viên',
        required=True,
        ondelete='cascade',
        index=True,
    )
    file_data = fields.Binary(
        string='File PDF',
        attachment=True,
        required=True,
    )
    file_name = fields.Char(string='Tên file')
    doc_type = fields.Selection([
        ('contract', 'Hợp đồng lao động'),
        ('id_card', 'CCCD / CMND'),
        ('decision', 'Quyết định'),
        ('other', 'Tài liệu khác'),
    ], string='Loại tài liệu', default='contract', required=True)
    upload_date = fields.Date(
        string='Ngày upload',
        default=fields.Date.context_today,
        required=True,
    )
    note = fields.Char(string='Ghi chú')
    company_id = fields.Many2one(
        'res.company',
        string='Công ty',
        related='employee_id.company_id',
        store=True,
        index=True,
    )

    def action_preview_pdf(self):
        self.ensure_one()
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'dl.employee.scan.doc',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(self.env.ref('dl_contract.view_dl_employee_scan_doc_form').id, 'form')],
            'target': 'new',
        }
