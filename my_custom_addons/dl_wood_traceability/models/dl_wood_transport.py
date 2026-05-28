# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
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
    _inherit = ['dl.wood.log.mixin']

    dossier_id = fields.Many2one('dl.wood.dossier', string='Hồ Sơ Gỗ', ondelete='cascade', required=True)
    company_id = fields.Many2one('res.company', related='dossier_id.company_id', store=True, readonly=True)
    
    vehicle_id = fields.Many2one('dl.wood.vehicle', string='Loại xe', required=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    vehicle_count = fields.Integer(string='Số lượng xe', required=True, default=1)
    
    total_nominal_capacity = fields.Float(string='Tổng sức chở (m³)', compute='_compute_total_capacity', store=True, digits=(16, 2))

    @api.depends('vehicle_id.capacity', 'vehicle_count')
    def _compute_total_capacity(self):
        for record in self:
            record.total_nominal_capacity = record.vehicle_count * record.vehicle_id.capacity if record.vehicle_id else 0.0

    def write(self, vals):
        for rec in self:
            if rec.dossier_id.state in ('using', 'summary', 'confirmed'):
                raise UserError(_("Không thể chỉnh sửa cấu hình xe vận chuyển khi Hồ sơ gỗ liên quan đang ở trạng thái '%s'.") % rec.dossier_id.state)
        return super(DlWoodDossierTransport, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('dossier_id'):
                dossier = self.env['dl.wood.dossier'].browse(vals['dossier_id'])
                if dossier.state in ('using', 'summary', 'confirmed'):
                    raise UserError(_("Không thể thêm cấu hình xe vận chuyển mới khi Hồ sơ gỗ liên quan đang ở trạng thái '%s'.") % dossier.state)
        return super(DlWoodDossierTransport, self).create(vals_list)

    def unlink(self):
        for rec in self:
            if rec.dossier_id.state in ('using', 'summary', 'confirmed'):
                raise UserError(_("Không thể xóa cấu hình xe vận chuyển khi Hồ sơ gỗ liên quan đang ở trạng thái '%s'.") % rec.dossier_id.state)
        return super(DlWoodDossierTransport, self).unlink()


class DlWoodDossierTransportTicket(models.Model):
    _name = 'dl.wood.dossier.transport.ticket'
    _description = 'Phiếu nhập kho'
    _order = 'name asc'

    dossier_id = fields.Many2one('dl.wood.dossier', string='Hồ Sơ Gỗ', ondelete='cascade', required=True)
    company_id = fields.Many2one('res.company', related='dossier_id.company_id', store=True, readonly=True)
    name = fields.Char(string='Tên phiếu', required=True)
    x_date = fields.Date(string='Ngày nhập kho')
    vehicle_count = fields.Integer(string='Số lượng xe', default=1)
    x_vehicle_info = fields.Char(string='Phương tiện sử dụng', help='Chi tiết các loại xe sử dụng trong chuyến này')
    x_vehicle_capacities = fields.Char(string='Tải trọng các xe (m³)', help='Danh sách tải trọng các xe cách nhau bằng dấu phẩy')
    
    fill_rate = fields.Float(string='Tỷ lệ lấp đầy', digits=(16, 4))
    total_volume = fields.Float(string='Tổng khối lượng (m³)', compute='_compute_total_volume', store=True, digits=(16, 1))
    
    ticket_line_ids = fields.One2many('dl.wood.dossier.transport.ticket.line', 'ticket_id', string='Chi tiết phiếu nhập kho')
    x_vehicle_ids = fields.One2many('dl.wood.dossier.transport.ticket.vehicle', 'ticket_id', string='Chi tiết phương tiện')

    @api.depends('ticket_line_ids.volume', 'x_vehicle_ids.volume')
    def _compute_total_volume(self):
        for record in self:
            if record.ticket_line_ids:
                record.total_volume = sum(record.ticket_line_ids.mapped('volume'))
            elif record.x_vehicle_ids:
                record.total_volume = sum(record.x_vehicle_ids.mapped('volume'))
            else:
                record.total_volume = 0.0

    def write(self, vals):
        for rec in self:
            if rec.dossier_id.state in ('using', 'summary', 'confirmed'):
                raise UserError(_("Không thể chỉnh sửa phiếu nhập kho khi Hồ sơ gỗ liên quan đang ở trạng thái '%s'.") % rec.dossier_id.state)
        return super(DlWoodDossierTransportTicket, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('dossier_id'):
                dossier = self.env['dl.wood.dossier'].browse(vals['dossier_id'])
                if dossier.state in ('using', 'summary', 'confirmed'):
                    raise UserError(_("Không thể thêm phiếu nhập kho mới khi Hồ sơ gỗ liên quan đang ở trạng thái '%s'.") % dossier.state)
        return super(DlWoodDossierTransportTicket, self).create(vals_list)

    def unlink(self):
        for rec in self:
            if rec.dossier_id.state in ('using', 'summary', 'confirmed'):
                raise UserError(_("Không thể xóa phiếu nhập kho khi Hồ sơ gỗ liên quan đang ở trạng thái '%s'.") % rec.dossier_id.state)
        return super(DlWoodDossierTransportTicket, self).unlink()


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

    def write(self, vals):
        for rec in self:
            if rec.dossier_id.state in ('using', 'summary', 'confirmed'):
                raise UserError(_("Không thể chỉnh sửa dòng lâm sản trong phiếu nhập kho khi Hồ sơ gỗ liên quan đang ở trạng thái '%s'.") % rec.dossier_id.state)
        return super(DlWoodDossierTransportTicketLine, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ticket_id'):
                ticket = self.env['dl.wood.dossier.transport.ticket'].browse(vals['ticket_id'])
                if ticket.dossier_id.state in ('using', 'summary', 'confirmed'):
                    raise UserError(_("Không thể thêm dòng lâm sản mới trong phiếu nhập kho khi Hồ sơ gỗ liên quan đang ở trạng thái '%s'.") % ticket.dossier_id.state)
        return super(DlWoodDossierTransportTicketLine, self).create(vals_list)

    def unlink(self):
        for rec in self:
            if rec.dossier_id.state in ('using', 'summary', 'confirmed'):
                raise UserError(_("Không thể xóa dòng lâm sản trong phiếu nhập kho khi Hồ sơ gỗ liên quan đang ở trạng thái '%s'.") % rec.dossier_id.state)
        return super(DlWoodDossierTransportTicketLine, self).unlink()


class DlWoodDossierTransportTicketVehicle(models.Model):
    _name = 'dl.wood.dossier.transport.ticket.vehicle'
    _description = 'Chi tiết phương tiện vận chuyển'
    _order = 'id asc'

    ticket_id = fields.Many2one('dl.wood.dossier.transport.ticket', string='Phiếu nhập kho', ondelete='cascade', required=True)
    dossier_id = fields.Many2one('dl.wood.dossier', related='ticket_id.dossier_id', store=True, readonly=True)
    company_id = fields.Many2one('res.company', related='ticket_id.company_id', store=True, readonly=True)
    
    name = fields.Char(string='Biển số xe', default='Chưa có biển số')
    capacity = fields.Float(string='Tải trọng thiết kế (m³)', required=True)
    volume = fields.Float(string='Khối lượng chở thực tế (m³)', required=True, digits=(16, 2))
    species_id = fields.Many2one('dl.wood.species', string='Loài gỗ', required=True)
    wood_type = fields.Selection([
        ('wood', 'Gỗ'),
        ('firewood', 'Củi')
    ], string='Phân loại', required=True)
    note = fields.Text(string='Ghi chú')

    def write(self, vals):
        for rec in self:
            if rec.dossier_id.state in ('using', 'summary', 'confirmed'):
                raise UserError(_("Không thể chỉnh sửa thông tin xe trong phiếu nhập kho khi Hồ sơ gỗ liên quan đang ở trạng thái '%s'.") % rec.dossier_id.state)
        return super(DlWoodDossierTransportTicketVehicle, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ticket_id'):
                ticket = self.env['dl.wood.dossier.transport.ticket'].browse(vals['ticket_id'])
                if ticket.dossier_id.state in ('using', 'summary', 'confirmed'):
                    raise UserError(_("Không thể thêm xe mới trong phiếu nhập kho khi Hồ sơ gỗ liên quan đang ở trạng thái '%s'.") % ticket.dossier_id.state)
        return super(DlWoodDossierTransportTicketVehicle, self).create(vals_list)

    def unlink(self):
        for rec in self:
            if rec.dossier_id.state in ('using', 'summary', 'confirmed'):
                raise UserError(_("Không thể xóa xe trong phiếu nhập kho khi Hồ sơ gỗ liên quan đang ở trạng thái '%s'.") % rec.dossier_id.state)
        return super(DlWoodDossierTransportTicketVehicle, self).unlink()


class DlWoodSaleOrderShipment(models.Model):
    _name = 'dl.wood.sale.order.shipment'
    _description = 'Chuyến xe vận chuyển Đơn đặt hàng'
    _order = 'shipping_date desc, id desc'

    sale_order_id = fields.Many2one('dl.wood.sale.order', string='Đơn đặt hàng', ondelete='cascade', required=True)
    shipping_date = fields.Date(string='Ngày xuất kho', default=fields.Date.context_today, required=True)
    vehicle_id = fields.Many2one('dl.wood.vehicle', string='Loại xe', required=True)
    license_plate = fields.Char(string='Biển số xe')
    line_ids = fields.One2many('dl.wood.sale.order.shipment.line', 'shipment_id', string='Chi tiết sản phẩm')
    
    total_volume = fields.Float(string='Tổng khối lượng (m³)', compute='_compute_total_volume', store=True, digits=(16, 2))
    x_allowed_production_order_ids = fields.Many2many('dl.wood.production.order', compute='_compute_allowed_production_orders', store=False)

    @api.depends('sale_order_id.production_order_ids')
    def _compute_allowed_production_orders(self):
        for rec in self:
            if rec.sale_order_id:
                rec.x_allowed_production_order_ids = rec.sale_order_id.production_order_ids
            else:
                rec.x_allowed_production_order_ids = False

    @api.depends('line_ids.qty')
    def _compute_total_volume(self):
        for rec in self:
            rec.total_volume = sum(rec.line_ids.mapped('qty'))

    def action_print_bkls(self):
        self.ensure_one()
        # Tính năng tải báo cáo Bảng kê lâm sản sẽ được triển khai chi tiết ở QWeb report sau.
        # Ở đây tạm thời raise Error để báo hiệu.
        raise UserError(_("Tính năng tải Bảng kê lâm sản bán ra đang được xây dựng!"))

    def action_print_receipt(self):
        self.ensure_one()
        raise UserError(_("Tính năng tải Phiếu biên nhận đang được xây dựng!"))


class DlWoodSaleOrderShipmentLine(models.Model):
    _name = 'dl.wood.sale.order.shipment.line'
    _description = 'Chi tiết sản phẩm vận chuyển'

    shipment_id = fields.Many2one('dl.wood.sale.order.shipment', string='Chuyến xe', ondelete='cascade', required=True)
    production_order_id = fields.Many2one('dl.wood.production.order', string='Lệnh sản xuất', required=True)
    product_id = fields.Many2one('product.product', related='production_order_id.product_id', string='Sản phẩm', store=True, readonly=True)
    qty = fields.Float(string='Khối lượng xuất chuyến này (m³)', required=True, digits=(16, 2))
    produced_qty = fields.Float(string='Khối lượng đã SX (m³)', related='production_order_id.qty_done', readonly=True, digits=(16, 2))

    @api.model
    def default_get(self, fields_list):
        res = super(DlWoodSaleOrderShipmentLine, self).default_get(fields_list)
        if 'production_order_id' in fields_list and not res.get('production_order_id'):
            sale_order_id = self.env.context.get('default_sale_order_id')
            if sale_order_id:
                sale_order = self.env['dl.wood.sale.order'].browse(sale_order_id)
                if sale_order.production_order_ids:
                    res['production_order_id'] = sale_order.production_order_ids[0].id
                    # Also populate other fields corresponding to this order
                    if 'qty' in fields_list:
                        res['qty'] = sale_order.production_order_ids[0].qty_done
        return res

    @api.onchange('production_order_id')
    def _onchange_production_order_id(self):
        if self.production_order_id:
            self.qty = self.production_order_id.qty_done

    @api.constrains('qty', 'product_id')
    def _check_qty(self):
        for rec in self:
            if rec.qty <= 0:
                raise UserError(_("Khối lượng vận chuyển phải lớn hơn 0."))
            # Tổng khối lượng vận chuyển của sản phẩm này trong đơn hàng không được vượt quá số lượng sản xuất
            sale_order = rec.shipment_id.sale_order_id
            if not sale_order:
                continue
            
            # Tính tổng khối lượng đã vận chuyển của sản phẩm này trong toàn bộ đơn hàng
            shipped_qty = sum(sale_order.shipment_ids.mapped('line_ids').filtered(lambda l: l.product_id == rec.product_id).mapped('qty'))
            
            # Tính tổng khối lượng của sản phẩm này trong các lệnh sản xuất thuộc đơn hàng
            produced_qty = sum(sale_order.production_order_ids.filtered(lambda p: p.product_id == rec.product_id).mapped('qty_done'))
            
            if shipped_qty > produced_qty:
                raise UserError(_("Tổng khối lượng vận chuyển của sản phẩm %s (%.2f m³) vượt quá tổng số lượng đã sản xuất (%.2f m³).") % (
                    rec.product_id.display_name, shipped_qty, produced_qty
                ))
