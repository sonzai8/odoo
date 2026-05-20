# -*- coding: utf-8 -*-
from odoo import models, fields, api
import random

class DlWoodVehicle(models.Model):
    _name = 'dl.wood.vehicle'
    _description = 'Phương tiện vận chuyển'

    name = fields.Char(string='Tên/Loại xe', required=True)
    capacity = fields.Float(string='Sức chở tối đa (m³)', required=True, digits=(16, 2))
    fill_rate_min = fields.Float(string='Tỷ lệ lấp đầy Min (%)', default=95.0, required=True, help="Tỷ lệ lấp đầy tối thiểu. Ví dụ: 95.0")
    fill_rate_max = fields.Float(string='Tỷ lệ lấp đầy Max (%)', default=98.9, required=True, help="Tỷ lệ lấp đầy tối đa. Ví dụ: 98.9")
    active = fields.Boolean(string='Đang hoạt động', default=True)
    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company)


class DlWoodDossierTransport(models.Model):
    _name = 'dl.wood.dossier.transport'
    _description = 'Cấu hình vận chuyển hồ sơ'

    dossier_id = fields.Many2one('dl.wood.dossier', string='Hồ Sơ Gỗ', ondelete='cascade', required=True)
    company_id = fields.Many2one('res.company', related='dossier_id.company_id', store=True, readonly=True)
    
    vehicle_id = fields.Many2one('dl.wood.vehicle', string='Loại xe', required=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    vehicle_count = fields.Integer(string='Số lượng xe', required=True, default=1)
    
    total_nominal_capacity = fields.Float(string='Tổng sức chở (m³)', compute='_compute_total_capacity', store=True, digits=(16, 2))

    @api.depends('vehicle_id.capacity', 'vehicle_count')
    def _compute_total_capacity(self):
        for record in self:
            record.total_nominal_capacity = record.vehicle_count * record.vehicle_id.capacity if record.vehicle_id else 0.0


class DlWoodDossierTransportTicket(models.Model):
    _name = 'dl.wood.dossier.transport.ticket'
    _description = 'Phiếu vận chuyển (Chuyến xe)'
    _order = 'name asc'

    dossier_id = fields.Many2one('dl.wood.dossier', string='Hồ Sơ Gỗ', ondelete='cascade', required=True)
    company_id = fields.Many2one('res.company', related='dossier_id.company_id', store=True, readonly=True)
    name = fields.Char(string='Tên chuyến', required=True)
    vehicle_count = fields.Integer(string='Số lượng xe', default=1)
    x_vehicle_info = fields.Char(string='Phương tiện sử dụng', help='Chi tiết các loại xe sử dụng trong chuyến này')
    
    fill_rate = fields.Float(string='Tỷ lệ lấp đầy', digits=(16, 4))
    total_volume = fields.Float(string='Tổng khối lượng (m³)', compute='_compute_total_volume', store=True, digits=(16, 1))
    
    ticket_line_ids = fields.One2many('dl.wood.dossier.transport.ticket.line', 'ticket_id', string='Chi tiết chuyến xe')

    @api.depends('ticket_line_ids.volume')
    def _compute_total_volume(self):
        for record in self:
            record.total_volume = sum(record.ticket_line_ids.mapped('volume'))


class DlWoodDossierTransportTicketLine(models.Model):
    _name = 'dl.wood.dossier.transport.ticket.line'
    _description = 'Chi tiết phân bổ trên chuyến xe'

    ticket_id = fields.Many2one('dl.wood.dossier.transport.ticket', string='Phiếu vận chuyển', ondelete='cascade', required=True)
    dossier_id = fields.Many2one('dl.wood.dossier', related='ticket_id.dossier_id', store=True, readonly=True)
    company_id = fields.Many2one('res.company', related='ticket_id.company_id', store=True, readonly=True)
    
    species_id = fields.Many2one('dl.wood.species', string='Loài gỗ', required=True)
    wood_type = fields.Selection([
        ('wood', 'Gỗ'),
        ('firewood', 'Củi')
    ], string='Phân loại', required=True)
    volume = fields.Float(string='Khối lượng (m³)', required=True, digits=(16, 1))
