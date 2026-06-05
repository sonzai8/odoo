# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta

class DlContract(models.Model):
    _name = 'dl.contract'
    _description = 'Hợp đồng lao động'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'

    name = fields.Char(string='Mã hợp đồng', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True, tracking=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", check_company=True)
    contract_type_id = fields.Many2one('dl.contract.type', string='Loại hợp đồng', required=True, tracking=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", check_company=True)
    
    date_start = fields.Date(string='Ngày bắt đầu hiệu lực', required=True, tracking=True, default=fields.Date.context_today)
    date_end = fields.Date(string='Ngày kết thúc', tracking=True)
    trial_date_end = fields.Date(string='Ngày kết thúc thử việc', tracking=True)
    
    wage = fields.Monetary(string='Lương cơ bản', tracking=True, help="Lương cơ bản trên hợp đồng")
    allowance = fields.Monetary(string='Phụ cấp', tracking=True)
    total_wage = fields.Monetary(string='Tổng thu nhập', compute='_compute_total_wage', store=True)
    
    job_title_id = fields.Many2one('dl.job.title', string='Chức danh', tracking=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    job_title = fields.Char(string='Chức danh trong HĐ', compute='_compute_job_title_char', store=True, readonly=False, tracking=True)
    department_id = fields.Many2one('hr.department', string='Phòng ban', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=True)
    
    scan_file = fields.Binary(string='File scan PDF hợp đồng', attachment=True)
    scan_filename = fields.Char(string='Tên file scan')
    
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('active', 'Đang hiệu lực'),
        ('expired', 'Hết hạn'),
        ('renewed', 'Đã gia hạn'),
        ('terminated', 'Chấm dứt')
    ], string='Trạng thái', default='draft', tracking=True, required=True, copy=False)
    
    previous_contract_id = fields.Many2one('dl.contract', string='Hợp đồng trước đó', readonly=True, copy=False)
    salary_history_ids = fields.One2many('dl.salary.history', 'contract_id', string='Lịch sử điều chỉnh lương')
    note = fields.Html(string='Ghi chú')
    
    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company, index=True)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', related='company_id.currency_id', readonly=True)
    
    x_days_to_expire = fields.Integer(string='Số ngày còn lại', compute='_compute_x_days_to_expire')
    x_is_expiring_soon = fields.Boolean(string='Sắp hết hạn', compute='_compute_x_days_to_expire')
    x_previous_state = fields.Char(string='Trạng thái trước đó', readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                company_id = vals.get('company_id', self.env.company.id)
                contract_type_id = vals.get('contract_type_id')
                if contract_type_id:
                    contract_type = self.env['dl.contract.type'].browse(contract_type_id)
                    code = (contract_type.code or '').strip()
                    if code:
                        seq_code = f'dl.contract.{code}'
                        seq = self.env['ir.sequence'].with_company(company_id).search([('code', '=', seq_code)], limit=1)
                        if not seq:
                            seq = self.env['ir.sequence'].sudo().create({
                                'name': f'Mã Hợp Đồng - {contract_type.name}',
                                'code': seq_code,
                                'prefix': f'DL-HD/{code}/%(year)s/',
                                'padding': 5,
                                'company_id': company_id,
                            })
                        seq_name = seq.with_company(company_id).next_by_id() or _('New')
                        vals['name'] = seq_name
                    else:
                        seq = self.env['ir.sequence'].with_company(company_id).next_by_code('dl.contract') or _('New')
                        vals['name'] = seq
                else:
                    seq = self.env['ir.sequence'].with_company(company_id).next_by_code('dl.contract') or _('New')
                    vals['name'] = seq
        return super().create(vals_list)

    @api.depends('wage', 'allowance')
    def _compute_total_wage(self):
        for record in self:
            record.total_wage = record.wage + record.allowance

    @api.depends('date_end', 'state')
    def _compute_x_days_to_expire(self):
        today = fields.Date.today()
        for record in self:
            if not record.date_end:
                record.x_days_to_expire = 99999
                record.x_is_expiring_soon = False
                continue
            
            delta = (record.date_end - today).days
            record.x_days_to_expire = delta
            
            # Tự động chuyển sang hết hạn nếu đã quá hạn kết thúc mà trạng thái vẫn là active
            if record.state == 'active' and delta < 0:
                record.state = 'expired'
            
            # Chỉ báo sắp hết hạn nếu đang hiệu lực và thời gian còn lại từ 0 đến 30 ngày
            record.x_is_expiring_soon = True if 0 <= delta <= 30 and record.state == 'active' else False

    @api.onchange('contract_type_id', 'date_start')
    def _onchange_contract_type_id(self):
        if self.contract_type_id:
            # 1. Tự động tính ngày kết thúc
            if self.date_start:
                if self.contract_type_id.duration_type == 'fixed':
                    months = self.contract_type_id.default_duration_months or 12
                    self.date_end = self.date_start + relativedelta(months=months, days=-1)
                else:
                    self.date_end = False
            
            # 2. Tự động lấy mức lương mặc định (nếu có)
            if self.contract_type_id.default_wage:
                self.wage = self.contract_type_id.default_wage

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            if getattr(self.employee_id, 'x_job_title_id', False):
                self.job_title_id = self.employee_id.x_job_title_id
            self.job_title = self.employee_id.job_title
            self.department_id = self.employee_id.department_id

    @api.onchange('job_title_id')
    def _onchange_job_title_id(self):
        if self.job_title_id and self.job_title_id.department_id:
            self.department_id = self.job_title_id.department_id

    @api.depends('job_title_id')
    def _compute_job_title_char(self):
        for record in self:
            if record.job_title_id:
                record.job_title = record.job_title_id.name

    def action_confirm(self):
        for record in self:
            if not record.date_start:
                raise ValidationError(_("Vui lòng nhập Ngày bắt đầu hiệu lực."))
            if record.wage <= 0:
                raise ValidationError(_("Lương cơ bản phải lớn hơn 0."))
            # Cập nhật lương ban đầu vào lịch sử
            if not record.salary_history_ids:
                self.env['dl.salary.history'].create({
                    'contract_id': record.id,
                    'old_wage': 0,
                    'new_wage': record.wage,
                    'effective_date': record.date_start,
                    'reason': 'Lương khởi điểm theo hợp đồng',
                })
            record.write({'state': 'active'})

    def action_expire(self):
        self.write({'state': 'expired'})

    def action_terminate(self):
        self.write({'state': 'terminated'})

    def action_renew(self):
        self.ensure_one()
        # Tạo hợp đồng mới trạng thái draft, copy thông tin
        new_contract = self.copy({
            'state': 'draft',
            'previous_contract_id': self.id,
            'date_start': self.date_end + relativedelta(days=1) if self.date_end else fields.Date.today(),
            'date_end': False,
            'name': _('New'),
            'scan_file': False,
            'scan_filename': False,
        })
        self.write({'state': 'renewed'})
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dl.contract',
            'view_mode': 'form',
            'res_id': new_contract.id,
            'target': 'current',
        }

    def write(self, vals):
        # Theo dõi thay đổi trạng thái để lưu trạng thái trước đó
        if 'state' in vals:
            for record in self:
                if record.state != vals['state']:
                    super(DlContract, record).write({'x_previous_state': record.state})

        # Theo dõi sự thay đổi lương để ghi vào lịch sử
        if 'wage' in vals:
            for record in self:
                if record.state != 'draft' and record.wage != vals['wage']:
                    self.env['dl.salary.history'].create({
                        'contract_id': record.id,
                        'old_wage': record.wage,
                        'new_wage': vals['wage'],
                        'effective_date': fields.Date.today(),
                        'reason': 'Điều chỉnh lương',
                    })
        return super(DlContract, self).write(vals)

    def action_set_to_previous_state(self):
        for record in self:
            if record.x_previous_state:
                prev_state = record.x_previous_state
                record.write({
                    'state': prev_state,
                    'x_previous_state': False
                })


    @api.model
    def _cron_check_expired(self):
        """Cron job chạy hàng ngày để kiểm tra và chuyển HĐ hết hạn"""
        today = fields.Date.today()
        expired_contracts = self.search([
            ('state', '=', 'active'),
            ('date_end', '<', today),
            ('date_end', '!=', False)
        ])
        if expired_contracts:
            expired_contracts.write({'state': 'expired'})
            # Có thể thêm logic tạo activity nhắc nhở HR ở đây
