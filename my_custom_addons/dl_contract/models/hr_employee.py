# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    dl_contract_ids = fields.One2many('dl.contract', 'employee_id', string='Danh sách hợp đồng', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    dl_contract_count = fields.Integer(string='Số lượng HĐ', compute='_compute_dl_contract_count')
    dl_current_contract_id = fields.Many2one('dl.contract', string='Hợp đồng hiện tại', compute='_compute_dl_current_contract_id', store=True)
    dl_contract_state = fields.Selection([
        ('no_contract', 'Chưa có hợp đồng'),
        ('active', 'Đang có hợp đồng'),
        ('expiring_soon', 'Sắp hết hợp đồng'),
        ('expired', 'Đã hết hạn/Chấm dứt')
    ], string='Tình trạng hợp đồng', compute='_compute_dl_contract_state', store=True)

    @api.depends('dl_contract_ids')
    def _compute_dl_contract_count(self):
        for employee in self:
            employee.dl_contract_count = len(employee.dl_contract_ids)

    @api.depends('dl_contract_ids.state', 'dl_contract_ids.date_start')
    def _compute_dl_current_contract_id(self):
        for employee in self:
            # Lấy hợp đồng đang hiệu lực gần nhất
            active_contracts = employee.dl_contract_ids.filtered(lambda c: c.state == 'active')
            if active_contracts:
                employee.dl_current_contract_id = active_contracts.sorted('date_start', reverse=True)[0]
            else:
                # Nếu không có cái nào active, lấy cái mới nhất (draft, renewed...)
                if employee.dl_contract_ids:
                    employee.dl_current_contract_id = employee.dl_contract_ids.sorted('date_start', reverse=True)[0]
                else:
                    employee.dl_current_contract_id = False

    @api.depends('dl_current_contract_id.state', 'dl_current_contract_id.x_is_expiring_soon')
    def _compute_dl_contract_state(self):
        for employee in self:
            contract = employee.dl_current_contract_id
            if not contract:
                employee.dl_contract_state = 'no_contract'
            elif contract.state == 'active':
                if contract.x_is_expiring_soon:
                    employee.dl_contract_state = 'expiring_soon'
                else:
                    employee.dl_contract_state = 'active'
            elif contract.state in ['expired', 'terminated']:
                employee.dl_contract_state = 'expired'
            else:
                employee.dl_contract_state = 'no_contract'

    def action_view_dl_contracts(self):
        self.ensure_one()
        return {
            'name': 'Hợp đồng lao động',
            'type': 'ir.actions.act_window',
            'res_model': 'dl.contract',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }
