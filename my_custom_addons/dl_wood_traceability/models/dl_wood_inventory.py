# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)

class DlWoodDossierInventory(models.Model):
    _name = 'dl.wood.dossier.inventory'
    _description = 'Phiếu kiểm kê hồ sơ gỗ'
    _order = 'date desc, id desc'

    name = fields.Char(string='Mã phiếu', required=True, copy=False, readonly=True, default=lambda self: _('Mới'))
    date = fields.Date(string='Ngày kiểm kê', default=fields.Date.context_today, required=True)
    user_id = fields.Many2one('res.users', string='Người thực hiện', default=lambda self: self.env.user, required=True, readonly=True)
    note = fields.Text(string='Ghi chú chung')
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('confirmed', 'Đang kiểm đếm'),
        ('done', 'Đã hoàn thành'),
        ('cancel', 'Đã hủy')
    ], string='Trạng thái', default='draft', index=True)

    line_ids = fields.One2many('dl.wood.dossier.inventory.line', 'inventory_id', string='Chi tiết kiểm kê')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Mới')) == _('Mới'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dl.wood.dossier.inventory') or _('Mới')
        return super().create(vals_list)

    def action_confirm(self):
        """Chốt số liệu tồn sổ sách (Snapshot) để bắt đầu kiểm đếm"""
        for rec in self:
            if rec.state != 'draft':
                continue
            for line in rec.line_ids:
                line.confirmed_theo_qty = line.dossier_id.remaining_qty
            rec.state = 'confirmed'
        return True

    def action_done(self):
        """Hoàn thành kiểm kê và ghi sổ cái Ledger"""
        for rec in self:
            if rec.state != 'confirmed':
                continue
            
            for line in rec.line_ids:
                diff = line.real_qty - line.theoretical_qty
                
                # 1. Cập nhật trạng thái hồ sơ nếu có chọn
                if line.new_state:
                    line.dossier_id.write({'state': line.new_state})

                # 2. Tạo dòng sổ cái điều chỉnh nếu có chênh lệch
                if diff != 0:
                    self.env['dl.dossier.ledger'].create({
                        'dossier_id': line.dossier_id.id,
                        'inventory_id': rec.id,
                        'qty_before': line.theoretical_qty,
                        'actual_qty': diff,
                        'qty_after': line.real_qty,
                        'note': f"Kiểm kê: {rec.name} - {line.reason or 'Điều chỉnh tồn kho'}",
                        'state': 'done',
                        'date': fields.Datetime.now(),
                    })
            rec.state = 'done'
        return True

    def action_cancel(self):
        """Hủy phiếu và tạo bản ghi hoàn trả nếu đã ghi sổ"""
        for rec in self:
            if rec.state == 'done':
                # Tạo bản ghi đối ứng hoàn trả tồn kho
                for line in rec.line_ids:
                    ledgers = self.env['dl.dossier.ledger'].search([
                        ('inventory_id', '=', rec.id), 
                        ('dossier_id', '=', line.dossier_id.id)
                    ])
                    for ledger in ledgers:
                        self.env['dl.dossier.ledger'].create({
                            'dossier_id': line.dossier_id.id,
                            'actual_qty': -ledger.actual_qty,
                            'note': f"Hoàn trả (Hủy phiếu kiểm kê): {rec.name}",
                            'state': 'done',
                            'date': fields.Datetime.now(),
                        })
                    # Gỡ liên kết để không tính trùng nếu phiếu này được phục hồi (nếu logic cho phép)
                    ledgers.write({'inventory_id': False})
            rec.state = 'cancel'
        return True

    def action_draft(self):
        for rec in self:
            if rec.state == 'cancel':
                rec.state = 'draft'
        return True

    def unlink(self):
        for rec in self:
            if rec.state in ['confirmed', 'done', 'cancel']:
                raise UserError(_("Không thể xóa phiếu kiểm kê đã xác nhận hoặc đã hủy. Vui lòng giữ lại để phục vụ truy soát (Audit Trail)."))
        return super().unlink()

class DlWoodDossierInventoryLine(models.Model):
    _name = 'dl.wood.dossier.inventory.line'
    _description = 'Chi tiết phiếu kiểm kê'

    inventory_id = fields.Many2one('dl.wood.dossier.inventory', string='Phiếu kiểm kê', ondelete='cascade')
    dossier_id = fields.Many2one('dl.wood.dossier', string='Hồ sơ gỗ', required=True, domain=[('state', '!=', 'closed')])
    
    # theoretical_qty hiển thị Real-time ở Draft, hiển thị Snapshot ở Confirmed/Done
    theoretical_qty = fields.Float(string='Tồn sổ sách (m³)', digits=(16, 2), compute='_compute_theoretical_qty')
    confirmed_theo_qty = fields.Float(string='Tồn chốt lúc kiểm (m³)', digits=(16, 2), readonly=True)
    
    real_qty = fields.Float(string='Tồn thực tế (m³)', digits=(16, 2), required=True)
    difference = fields.Float(string='Chênh lệch (m³)', compute='_compute_difference', digits=(16, 2))
    
    current_state = fields.Selection(related='dossier_id.state', string='Trạng thái hiện tại', readonly=True)
    new_state = fields.Selection([
        ('exploiting', 'Đang Khai Thác'),
        ('in_use', 'Đang Sử Dụng'),
        ('summary', 'Tổng Kết'),
        ('closed', 'Đóng')
    ], string='Cập nhật trạng thái')

    reason = fields.Char(string='Lý do điều chỉnh')

    @api.depends('inventory_id.state', 'dossier_id.remaining_qty', 'confirmed_theo_qty')
    def _compute_theoretical_qty(self):
        for line in self:
            if line.inventory_id.state in ['confirmed', 'done', 'cancel']:
                line.theoretical_qty = line.confirmed_theo_qty
            else:
                line.theoretical_qty = line.dossier_id.remaining_qty

    @api.onchange('dossier_id')
    def _onchange_dossier_id(self):
        if self.dossier_id:
            self.real_qty = self.dossier_id.remaining_qty

    @api.depends('theoretical_qty', 'real_qty')
    def _compute_difference(self):
        for line in self:
            line.difference = line.real_qty - line.theoretical_qty
