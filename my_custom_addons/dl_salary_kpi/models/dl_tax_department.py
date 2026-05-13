# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.models import Constraint

class DlTaxDepartment(models.Model):
    _name = 'dl.tax.department'
    _description = 'Phòng ban thuế'
    _order = 'sequence, name'

    name = fields.Char(string='Tên phòng ban', required=True)
    code = fields.Char(string='Mã phòng ban')
    sequence = fields.Integer(string='Thứ tự', default=10)
    active = fields.Boolean(string='Đang hoạt động', default=True)
    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company)

    @api.model
    def _seed_default_data(self):
        """Hàm hỗ trợ khởi tạo dữ liệu an toàn, gọi từ XML function."""
        # Danh sách phòng ban chuẩn
        tax_depts = [
            {'name': 'Quản Lý', 'sequence': 10},
            {'name': 'Kinh Doanh', 'sequence': 20},
            {'name': 'Lái Xe', 'sequence': 30},
            {'name': 'Công Nhật', 'sequence': 40},
            {'name': 'Quản Lý Sản Xuất', 'sequence': 50},
            {'name': 'Sản Xuất', 'sequence': 60},
        ]
        
        companies = self.env['res.company'].sudo().search([])
        for company in companies:
            for dept in tax_depts:
                # Kiểm tra xem phòng ban này đã tồn tại trong công ty chưa
                existing = self.sudo().search([
                    ('name', '=', dept['name']),
                    ('company_id', '=', company.id)
                ], limit=1)
                
                if not existing:
                    self.sudo().create({
                        'name': dept['name'],
                        'sequence': dept['sequence'],
                        'company_id': company.id
                    })
        return True

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        domain = domain or []
        if name:
            # Ưu tiên tìm trong công ty hiện tại trước
            company_domain = [('name', operator, name), ('company_id', '=', self.env.company.id)]
            ids = self._search(company_domain + domain, limit=limit, order=order)
            if ids:
                return ids
        return super()._name_search(name, domain=domain, operator=operator, limit=limit, order=order)

    _name_company_unique = models.Constraint(
        'unique(name, company_id)',
        'Tên phòng ban đã tồn tại trong công ty này!'
    )
