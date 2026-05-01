# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date, timedelta

class EmployeeTransfer(models.Model):
    _name = 'dl.employee.transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Lệnh điều chuyển nhân sự'
    _order = 'date_request desc'

    employee_id = fields.Many2one(
        'hr.employee', 
        string='Nhân viên', 
        required=True, 
        tracking=True
    )
    from_group_id = fields.Many2one(
        'dl.production.group', 
        string='Tổ gốc cũ', 
        readonly=True
    )
    to_group_id = fields.Many2one(
        'dl.production.group', 
        string='Tổ gốc mới', 
        required=True, 
        tracking=True
    )
    date_request = fields.Date(
        string='Ngày yêu cầu', 
        default=fields.Date.today(), 
        readonly=True
    )
    date_effective = fields.Date(
        string='Ngày hiệu lực', 
        tracking=True,
        help='Ngày chính thức chuyển sang tổ mới'
    )
    transfer_type = fields.Selection([
        ('immediate', 'Ngay lập tức'),
        ('next_month', 'Ngày 1 tháng sau'),
        ('custom', 'Ngày tùy chọn')
    ], string='Cấu hình ngày chuyển', default='next_month', required=True, tracking=True)
    
    custom_date = fields.Date(string='Ngày cụ thể')

    state = fields.Selection([
        ('draft', 'Mới'),
        ('scheduled', 'Đã hẹn'),
        ('done', 'Đã hoàn tất'),
        ('cancel', 'Đã hủy')
    ], string='Trạng thái', default='draft', tracking=True)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.from_group_id = self.employee_id.x_source_group_id

    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                continue
            
            # Kiểm tra xem nhân viên có lệnh điều chuyển nào đang chờ không
            pending = self.search([
                ('employee_id', '=', rec.employee_id.id),
                ('state', '=', 'scheduled'),
                ('id', '!=', rec.id)
            ])
            if pending:
                raise UserError(_("Nhân viên %s đang có một lệnh điều chuyển khác chờ xử lý!") % rec.employee_id.name)

            today = date.today()
            if rec.transfer_type == 'immediate':
                rec.date_effective = today
                # Thực hiện chuyển ngay
                rec._do_transfer()
                rec.state = 'done'
            elif rec.transfer_type == 'next_month':
                # Ngày 01 của tháng kế tiếp
                rec.date_effective = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
                rec.state = 'scheduled'
            elif rec.transfer_type == 'custom':
                if not rec.custom_date:
                    raise UserError(_("Vui lòng chọn ngày cụ thể!"))
                rec.date_effective = rec.custom_date
                if rec.date_effective <= today:
                    # Nếu ngày chọn là quá khứ hoặc hôm nay, thực hiện ngay
                    rec._do_transfer()
                    rec.state = 'done'
                else:
                    rec.state = 'scheduled'

    def _do_transfer(self):
        self.ensure_one()
        self.employee_id.write({
            'x_source_group_id': self.to_group_id.id
        })
        self.employee_id.message_post(body=_(
            "Đã thực hiện điều chuyển từ tổ %s sang tổ %s theo lệnh %s"
        ) % (self.from_group_id.name or 'Trống', self.to_group_id.name, self.id))

    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.model
    def _cron_process_transfers(self):
        """Tiến trình xử lý các lệnh điều chuyển đến ngày hiệu lực"""
        today = fields.Date.today()
        transfers = self.search([
            ('state', '=', 'scheduled'),
            ('date_effective', '<=', today)
        ])
        for transfer in transfers:
            try:
                transfer._do_transfer()
                transfer.write({'state': 'done'})
            except Exception as e:
                # Log lỗi nếu có
                self.env['ir.logging'].create({
                    'name': 'dl.employee.transfer',
                    'type': 'server',
                    'level': 'error',
                    'message': f"Error processing transfer {transfer.id}: {str(e)}",
                    'path': 'dl_wood_payroll',
                    'line': '0',
                    'func': '_cron_process_transfers'
                })
