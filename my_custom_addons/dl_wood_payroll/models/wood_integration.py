from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_thickness = fields.Float(related='product_id.x_thickness', string='Dày (mm)', readonly=True)
    x_length = fields.Float(related='product_id.x_length', string='Dài (mm)', readonly=True)
    x_width = fields.Float(related='product_id.x_width', string='Rộng (mm)', readonly=True)
    x_structure_summary = fields.Char(related='product_id.x_structure_summary', string='Thông số kỹ thuật', readonly=True)

class StockMove(models.Model):
    _inherit = 'stock.move'

    x_thickness = fields.Float(related='product_id.x_thickness', string='Dày (mm)', readonly=True)
    x_length = fields.Float(related='product_id.x_length', string='Dài (mm)', readonly=True)
    x_width = fields.Float(related='product_id.x_width', string='Rộng (mm)', readonly=True)
    x_structure_summary = fields.Char(related='product_id.x_structure_summary', string='Thông số kỹ thuật', readonly=True)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_thickness = fields.Float(related='product_id.x_thickness', string='Dày (mm)', readonly=True)
    x_length = fields.Float(related='product_id.x_length', string='Dài (mm)', readonly=True)
    x_width = fields.Float(related='product_id.x_width', string='Rộng (mm)', readonly=True)
    x_structure_summary = fields.Char(related='product_id.x_structure_summary', string='Thông số kỹ thuật', readonly=True)
