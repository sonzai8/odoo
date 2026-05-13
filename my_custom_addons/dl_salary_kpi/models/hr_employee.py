# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Override name
    
    dl_first_name = fields.Char(string="Tên riêng", help="Nhập tên riêng của nhân viên")
    dl_tax_id = fields.Char(string='Mã số thuế')
    dl_tax_department_id = fields.Many2one(
        'dl.tax.department', 
        string='Phòng ban thuế',
        check_company=True,
        domain="[('company_id', '=', company_id)]"
    )
    dl_tax_position = fields.Char(string='Chức vụ thuế')
    dl_tax_base_salary = fields.Float(string='Lương cơ bản thuế')
    dl_departure_date = fields.Date(string='Ngày nghỉ việc')
    dependent_ids = fields.One2many('dl.dependent', 'employee_id', string='Người phụ thuộc')

    x_bank_account = fields.Char(string='Số Tài Khoản')
    x_bank_name = fields.Char(string='Tên Ngân Hàng')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._fix_tax_department_company(vals)
        return super().create(vals_list)

    def write(self, vals):
        if 'dl_tax_department_id' in vals or 'company_id' in vals:
            # Nếu đang update hàng loạt nhiều nhân viên, chúng ta cần xử lý từng cái
            for rec in self:
                temp_vals = vals.copy()
                # Cần context của từng record để biết company_id hiện tại nếu không có trong vals
                rec._fix_tax_department_company(temp_vals)
                super(HrEmployee, rec).write(temp_vals)
            return True
        return super().write(vals)

    def _fix_tax_department_company(self, vals):
        """Nếu phòng ban thuế không thuộc công ty của nhân viên, tìm phòng ban cùng tên ở đúng công ty."""
        dept_id = vals.get('dl_tax_department_id')
        company_id = vals.get('company_id') or (self.company_id.id if self else False)
        
        if dept_id and company_id:
            dept = self.env['dl.tax.department'].sudo().browse(dept_id)
            if dept.exists() and dept.company_id.id != company_id:
                # Mismatch! Try to find same name in correct company
                correct_dept = self.env['dl.tax.department'].sudo().search([
                    ('name', '=', dept.name),
                    ('company_id', '=', company_id)
                ], limit=1)
                if correct_dept:
                    vals['dl_tax_department_id'] = correct_dept.id

    @api.onchange('x_bank_name')
    def _onchange_x_bank_name(self):
        if self.x_bank_name:
            self.x_bank_name = self.x_bank_name.upper()
