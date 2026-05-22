# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_wood_product = fields.Boolean(
        string='Là sản phẩm Gỗ', 
        help='Nếu chọn, sản phẩm sẽ bắt buộc quản lý theo Lô (Lot).',
        default=False
    )
    x_woodpro_id = fields.Char(string='ID WoodPro', index=True)
    x_production_order_count = fields.Integer(
        string='Số lệnh sản xuất',
        compute='_compute_x_production_order_count'
    )

    @api.depends('product_variant_ids')
    def _compute_x_production_order_count(self):
        for rec in self:
            variants = rec.product_variant_ids
            rec.x_production_order_count = self.env['dl.wood.production.order'].search_count([
                ('product_id', 'in', variants.ids)
            ])

    def action_view_production_orders(self):
        self.ensure_one()
        variants = self.product_variant_ids
        return {
            'name': _('Lệnh sản xuất - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'dl.wood.production.order',
            'view_mode': 'list,form',
            'domain': [('product_id', 'in', variants.ids)],
            'context': {
                'default_product_id': self.product_variant_id.id if self.product_variant_id else False,
            }
        }

    def action_create_production_order(self):
        self.ensure_one()
        return {
            'name': _('Tạo mới Lệnh sản xuất'),
            'type': 'ir.actions.act_window',
            'res_model': 'dl.wood.production.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_product_id': self.product_variant_id.id if self.product_variant_id else False,
            }
        }

    @api.onchange('is_wood_product')
    def _onchange_is_wood_product(self):
        """Tự động thiết lập quản lý theo Lô khi tích chọn là sản phẩm Gỗ"""
        if self.is_wood_product:
            self.tracking = 'lot'


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _compute_display_name(self):
        super()._compute_display_name()
        for product in self:
            is_wood = product.product_tmpl_id.is_wood_product or getattr(product, 'x_is_wood_product', False)
            if is_wood and product.default_code:
                code = product.default_code.strip()
                if code:
                    name = product.name or ''
                    spec = getattr(product.product_tmpl_id, 'x_structure_summary', False)
                    # Định dạng: [Mã] Tên [Thông số kỹ thuật]
                    if spec:
                        product.display_name = f"[{code}] {name} [{spec}]"
                    else:
                        product.display_name = f"[{code}] {name}"
