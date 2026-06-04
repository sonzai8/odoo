class DlWoodSaleOrderShipment(models.Model):
    _name = 'dl.wood.sale.order.shipment'
    _description = 'Chuyến xe vận chuyển Đơn đặt hàng'
    _order = 'shipping_date desc, id desc'

    sale_order_id = fields.Many2one('dl.wood.sale.order', string='Đơn đặt hàng', ondelete='cascade', required=True)
    shipping_date = fields.Date(string='Ngày xuất kho', default=fields.Date.context_today, required=True)
    vehicle_id = fields.Many2one('dl.wood.vehicle', string='Loại xe', required=True)
    license_plate = fields.Char(string='Biển số xe')
    receipt_file = fields.Binary(string='Phiếu biên nhận', attachment=True)
    receipt_file_name = fields.Char(string='Tên file biên nhận')
    line_ids = fields.One2many('dl.wood.sale.order.shipment.line', 'shipment_id', string='Chi tiết sản phẩm')
    
    total_volume = fields.Float(string='Tổng khối lượng (m³)', compute='_compute_total_volume', store=True, digits=(16, 2))

    @api.depends('line_ids.qty')
    def _compute_total_volume(self):
        for rec in self:
            rec.total_volume = sum(rec.line_ids.mapped('qty'))

    def action_print_bkls(self):
        self.ensure_one()
        # Tính năng tải báo cáo Bảng kê lâm sản sẽ được triển khai chi tiết ở QWeb report sau.
        # Ở đây tạm thời raise Error để báo hiệu.
        raise UserError(_("Tính năng tải Bảng kê lâm sản bán ra đang được xây dựng!"))


class DlWoodSaleOrderShipmentLine(models.Model):
    _name = 'dl.wood.sale.order.shipment.line'
    _description = 'Chi tiết sản phẩm vận chuyển'

    shipment_id = fields.Many2one('dl.wood.sale.order.shipment', string='Chuyến xe', ondelete='cascade', required=True)
    product_id = fields.Many2one('product.product', string='Sản phẩm', required=True)
    qty = fields.Float(string='Khối lượng (m³)', required=True, digits=(16, 2))

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
