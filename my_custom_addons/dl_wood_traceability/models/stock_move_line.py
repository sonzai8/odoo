# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.constrains('lot_id', 'lot_name', 'state')
    def _check_wood_product_lot(self):
        """Bắt buộc nhập số Lô đối với sản phẩm ngành Gỗ khi hoàn thành"""
        for line in self:
            if line.state == 'done' and line.product_id.x_is_wood_product:
                if not line.lot_id and not line.lot_name:
                    raise ValidationError(_(
                        "Sản phẩm '%s' được cấu hình là sản phẩm Gỗ. "
                        "Bạn bắt buộc phải nhập số Lô (Lot Number) trước khi hoàn thành."
                    ) % line.product_id.display_name)
