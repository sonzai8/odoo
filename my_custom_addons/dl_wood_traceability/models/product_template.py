# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

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

    @api.onchange('x_required_peeling_type_ids')
    def _onchange_wood_name_and_code_traceability(self):
        if hasattr(self, '_onchange_wood_name_and_code'):
            self._onchange_wood_name_and_code()

    def write(self, vals):
        if self.env.context.get('misa_sync'):
            return super(ProductTemplate, self).write(vals)
            
        # Danh sách các trường không được phép sửa nếu là sản phẩm MISA
        blocked_fields = {
            'name', 'default_code', 'list_price', 'standard_price', 'uom_id', 'uom_po_id', 
            'type', 'categ_id', 'x_is_wood_product', 'x_thickness', 'x_width', 'x_length',
            'x_required_peeling_type_ids', 'barcode'
        }
        
        if any(f in vals for f in blocked_fields):
            for rec in self:
                if rec.x_is_misa_synced:
                    from odoo.exceptions import UserError
                    raise UserError("Sản phẩm này được đồng bộ từ MISA. Hệ thống không cho phép sửa đổi các thuộc tính của sản phẩm để đảm bảo tính nhất quán dữ liệu!")
                    
        return super(ProductTemplate, self).write(vals)

    x_woodpro_id = fields.Char(string='ID WoodPro', index=True)
    x_is_misa_synced = fields.Boolean(string='Đồng bộ từ MISA', default=False, readonly=True)

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

    @api.onchange('x_is_wood_product')
    def _onchange_x_is_wood_product(self):
        """Tự động thiết lập quản lý theo Lô khi tích chọn là sản phẩm Gỗ"""
        if hasattr(self, 'x_is_wood_product') and self.x_is_wood_product:
            self.tracking = 'lot'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('x_is_wood_product'):
                if 'company_id' not in vals or not vals['company_id']:
                    vals['company_id'] = self.env.company.id
        return super(ProductTemplate, self).create(vals_list)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    x_required_species_ids = fields.Many2many(related='product_tmpl_id.x_required_species_ids', readonly=True)
    x_required_peeling_type_ids = fields.Many2many(related='product_tmpl_id.x_required_peeling_type_ids', readonly=True)

    def _compute_display_name(self):
        super()._compute_display_name()
        for product in self:
            is_wood = product.product_tmpl_id.x_is_wood_product or getattr(product, 'x_is_wood_product', False)
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

    def write(self, vals):
        if self.env.context.get('misa_sync'):
            return super(ProductProduct, self).write(vals)
            
        blocked_fields = {
            'name', 'default_code', 'list_price', 'standard_price', 'uom_id', 'uom_po_id', 
            'type', 'categ_id', 'barcode'
        }
        
        if any(f in vals for f in blocked_fields):
            for rec in self:
                if getattr(rec.product_tmpl_id, 'x_is_misa_synced', False):
                    from odoo.exceptions import UserError
                    raise UserError("Biến thể này thuộc sản phẩm được đồng bộ từ MISA. Hệ thống không cho phép sửa đổi các thuộc tính cốt lõi!")
                    
        return super(ProductProduct, self).write(vals)
