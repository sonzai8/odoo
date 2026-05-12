# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class DlLinkProductionWizard(models.TransientModel):
    _name = 'dl.link.production.wizard'
    _description = 'Wizard gán lệnh sản xuất vào đơn hàng'

    sale_order_id = fields.Many2one('dl.wood.sale.order', string='Đơn bán hàng', required=True)
    production_order_ids = fields.Many2many(
        'dl.wood.production.order', 
        string='Chọn lệnh sản xuất',
        domain="[('sale_order_id', '=', False)]",
        help="Chỉ hiển thị các lệnh sản xuất chưa được gán vào đơn hàng nào."
    )

    def action_link_productions(self):
        self.ensure_one()
        if self.production_order_ids:
            # Gán SO vào các LSX đã chọn
            self.production_order_ids.write({'sale_order_id': self.sale_order_id.id})
            
            # Cập nhật lại khách hàng cho LSX nếu SO đã có khách hàng
            if self.sale_order_id.partner_id:
                self.production_order_ids.write({'partner_id': self.sale_order_id.partner_id.id})
                
        return {'type': 'ir.actions.client', 'tag': 'reload'}
