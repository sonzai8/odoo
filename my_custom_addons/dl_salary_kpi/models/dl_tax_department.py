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
    def _seed_default_data(self, company_id=None):
        """Hàm hỗ trợ khởi tạo dữ liệu an toàn cho một hoặc tất cả công ty."""
        tax_depts = [
            {'name': 'Quản Lý', 'sequence': 10},
            {'name': 'Kinh Doanh', 'sequence': 20},
            {'name': 'Lái Xe', 'sequence': 30},
            {'name': 'Công Nhật', 'sequence': 40},
            {'name': 'Quản Lý Sản Xuất', 'sequence': 50},
            {'name': 'Sản Xuất', 'sequence': 60},
        ]
        
        # Nếu không truyền company_id, lấy công ty hiện tại
        target_company_ids = [company_id] if company_id else [self.env.company.id]
        
        for comp_id in target_company_ids:
            for dept in tax_depts:
                # QUAN TRỌNG: Dùng active_test=False để tìm cả bản ghi đã bị ẩn (Archived)
                # Tránh lỗi Unique Constraint khi tạo mới trùng tên với bản ghi cũ
                existing = self.sudo().with_context(active_test=False).search([
                    ('name', '=', dept['name']),
                    ('company_id', '=', comp_id)
                ], limit=1)
                
                if not existing:
                    self.sudo().create({
                        'name': dept['name'],
                        'sequence': dept['sequence'],
                        'company_id': comp_id
                    })
                elif not existing.active:
                    # Nếu tồn tại nhưng đang bị ẩn, kích hoạt lại thay vì tạo mới
                    existing.sudo().write({'active': True})
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
