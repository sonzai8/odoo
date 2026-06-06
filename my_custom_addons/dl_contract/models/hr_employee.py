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
    x_active_contract_type_id = fields.Many2one('dl.contract.type', string='Loại hợp đồng', compute='_compute_active_contract_info', store=True)
    x_active_contract_department_id = fields.Many2one('hr.department', string='Phòng ban (HĐ)', compute='_compute_active_contract_info', store=True)
    x_active_contract_job_title = fields.Char(string='Chức danh (HĐ)', compute='_compute_active_contract_info', store=True)

    x_cccd_date = fields.Date(string='Ngày cấp CCCD')
    x_cccd_place = fields.Selection([
        ('cuc_qlhc', 'CCS QLHC về TTXH'),
        ('bo_cong_an', 'Bộ công an')
    ], string='Nơi cấp CCCD', default='cuc_qlhc')
    x_job_title_id = fields.Many2one('dl.job.title', string='Chức danh', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    # Bảo hiểm & Hộ gia đình
    x_kcb_state_id = fields.Many2one(
        'res.country.state', 
        string='Tỉnh đăng ký KCB ban đầu', 
        domain="[('country_id.code', '=', 'VN')]",
        compute='_compute_x_kcb_state_id',
        store=True,
        readonly=False
    )
    x_kcb_hospital = fields.Char(
        string='Bệnh viện đăng ký KCB ban đầu',
        compute='_compute_x_kcb_hospital',
        store=True,
        readonly=False
    )
    x_household_code = fields.Char(string='Mã số hộ gia đình')

    # Thông tin khai sinh / nơi sinh
    x_birth_state_id = fields.Many2one(
        'res.country.state', 
        string='Tỉnh khai sinh', 
        domain="[('country_id.code', '=', 'VN')]"
    )
    x_birth_ward_id = fields.Many2one(
        'res.country.ward', 
        string='Xã/Phường khai sinh', 
        domain="[('state_id', '=', x_birth_state_id)]"
    )
    x_birth_address = fields.Char(string='Nơi sinh (chi tiết)')

    # Tab Tài liệu scan
    dl_scan_doc_ids = fields.One2many(
        'dl.employee.scan.doc',
        'employee_id',
        string='Tài liệu Scan',
    )
    dl_scan_doc_count = fields.Integer(
        string='Số tài liệu scan',
        compute='_compute_dl_scan_doc_count',
    )
    dl_family_member_ids = fields.One2many(
        'dl.employee.family.member',
        'employee_id',
        string='Thành viên Gia đình'
    )

    @api.model
    def default_get(self, fields_list):
        res = super(HrEmployee, self).default_get(fields_list)
        company_id = res.get('company_id') or self.env.company.id
        if company_id:
            company = self.env['res.company'].browse(company_id)
            if 'x_kcb_state_id' in fields_list and not res.get('x_kcb_state_id'):
                res['x_kcb_state_id'] = company.x_kcb_state_id.id
            if 'x_kcb_hospital' in fields_list and not res.get('x_kcb_hospital'):
                res['x_kcb_hospital'] = company.x_kcb_hospital
        return res

    @api.depends('dl_contract_ids')
    def _compute_dl_contract_count(self):
        for employee in self:
            employee.dl_contract_count = len(employee.dl_contract_ids)

    @api.depends('dl_scan_doc_ids')
    def _compute_dl_scan_doc_count(self):
        for employee in self:
            employee.dl_scan_doc_count = len(employee.dl_scan_doc_ids)

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

    @api.onchange('x_job_title_id')
    def _onchange_x_job_title_id(self):
        if self.x_job_title_id:
            self.job_title = self.x_job_title_id.name
            if self.x_job_title_id.department_id:
                self.department_id = self.x_job_title_id.department_id

    @api.depends('dl_contract_ids.state', 'dl_contract_ids.department_id', 'dl_contract_ids.job_title', 'dl_contract_ids.contract_type_id', 'dl_contract_ids.date_start')
    def _compute_active_contract_info(self):
        for employee in self:
            active_contracts = employee.dl_contract_ids.filtered(lambda c: c.state == 'active')
            if active_contracts:
                latest_active = active_contracts.sorted('date_start', reverse=True)[0]
                employee.x_active_contract_department_id = latest_active.department_id
                employee.x_active_contract_job_title = latest_active.job_title
                employee.x_active_contract_type_id = latest_active.contract_type_id.id
            else:
                employee.x_active_contract_department_id = False
                employee.x_active_contract_job_title = False
                employee.x_active_contract_type_id = False

    @api.depends('company_id')
    def _compute_x_kcb_state_id(self):
        for rec in self:
            if rec.company_id and not rec.x_kcb_state_id:
                rec.x_kcb_state_id = rec.company_id.x_kcb_state_id
            elif not rec.company_id:
                rec.x_kcb_state_id = False

    @api.depends('company_id')
    def _compute_x_kcb_hospital(self):
        for rec in self:
            if rec.company_id and not rec.x_kcb_hospital:
                rec.x_kcb_hospital = rec.company_id.x_kcb_hospital
            elif not rec.company_id:
                rec.x_kcb_hospital = False

    @api.onchange('company_id')
    def _onchange_company_id_kcb(self):
        if self.company_id:
            self.x_kcb_state_id = self.company_id.x_kcb_state_id
            self.x_kcb_hospital = self.company_id.x_kcb_hospital
        else:
            self.x_kcb_state_id = False
            self.x_kcb_hospital = False

    @api.onchange('x_birth_state_id')
    def _onchange_x_birth_state_id(self):
        if self.x_birth_state_id:
            if self.x_birth_ward_id and self.x_birth_ward_id.state_id != self.x_birth_state_id:
                self.x_birth_ward_id = False
        else:
            self.x_birth_ward_id = False


