# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_wood_product = fields.Boolean(
        string='Là sản phẩm Gỗ', 
        help='Nếu chọn, sản phẩm sẽ bắt buộc quản lý theo Lô (Lot).',
        default=False
    )
    x_thickness = fields.Float(string='Độ dày (mm)', digits=(16, 2))
    x_length = fields.Float(string='Chiều dài (mm)', digits=(16, 1), default=2440.0)
    x_width = fields.Float(string='Chiều rộng (mm)', digits=(16, 1), default=1220.0)
    
    x_area_m2 = fields.Float(string='Diện tích (m2)', compute='_compute_wood_measurements', store=True)
    x_volume_m3 = fields.Float(string='Khối lượng (m3)', compute='_compute_wood_measurements', store=True)

    x_required_species_ids = fields.Many2many(
        'dl.wood.species', string='Loại gỗ bắt buộc',
        compute='_compute_x_required_species_ids', store=True,
        help='Tự động suy ra từ Loại ván bóc.'
    )

    @api.depends('x_required_peeling_type_ids')
    def _compute_x_required_species_ids(self):
        for rec in self:
            rec.x_required_species_ids = rec.x_required_peeling_type_ids.mapped('species_id')
    x_required_peeling_type_ids = fields.Many2many(
        'dl.wood.peeling.type',
        string='Loại Ván bóc',
        help='Chỉ cần chọn Loại Ván Bóc gốc (Keo, Bạch Đàn...), không cần quan tâm độ dày.'
    )

    x_woodpro_id = fields.Char(string='ID WoodPro', index=True)

    @api.depends('x_length', 'x_width', 'x_thickness')
    def _compute_wood_measurements(self):
        for product in self:
            area = (product.x_length * product.x_width) / 1000000.0
            product.x_area_m2 = area
            product.x_volume_m3 = (area * product.x_thickness) / 1000.0
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_wood_product'):
                if 'company_id' not in vals or not vals['company_id']:
                    vals['company_id'] = self.env.company.id
        return super(ProductTemplate, self).create(vals_list)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    x_thickness = fields.Float(related='product_tmpl_id.x_thickness', readonly=True)
    x_length = fields.Float(related='product_tmpl_id.x_length', readonly=True)
    x_width = fields.Float(related='product_tmpl_id.x_width', readonly=True)
    x_area_m2 = fields.Float(related='product_tmpl_id.x_area_m2', readonly=True)
    x_volume_m3 = fields.Float(related='product_tmpl_id.x_volume_m3', readonly=True)
    x_required_species_ids = fields.Many2many(related='product_tmpl_id.x_required_species_ids', readonly=True)
    x_required_peeling_type_ids = fields.Many2many(related='product_tmpl_id.x_required_peeling_type_ids', readonly=True)

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
