# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class DlWoodSaleOrder(models.Model):
    """Đơn đặt hàng gỗ thành phẩm từ khách hàng."""
    _name = 'dl.wood.sale.order'
    _description = 'Đơn đặt hàng gỗ'
    _order = 'date_order desc, name desc'

    name = fields.Char(
        string='Mã đơn hàng', required=True, copy=False,
        default=lambda self: _('Mới'), index=True
    )
    
    _name_company_unique = models.Constraint(
        'unique(name, company_id)',
        'Mã đơn hàng đã tồn tại trong công ty này!'
    )
    partner_id = fields.Many2one(
        'res.partner', string='Khách hàng', required=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), ('x_is_wood_customer', '=', True)]",
        index=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Công ty',
        required=True,
        default=lambda self: self.env.company
    )
    date_order = fields.Date(string='Ngày đặt hàng', default=fields.Date.context_today)
    x_invoice_code = fields.Char(string='Số hóa đơn', index=True)
    x_woodpro_id = fields.Char(string='ID WoodPro', index=True)
    note = fields.Text(string='Ghi chú')
    production_order_ids = fields.One2many(
        'dl.wood.production.order', 'sale_order_id',
        string='Lệnh sản xuất'
    )
    production_count = fields.Integer(
        string='Số lệnh SX', compute='_compute_production_count'
    )
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('confirmed', 'Đã xác nhận'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Đã hủy'),
    ], string='Trạng thái', default='draft', index=True)

    @api.depends('production_order_ids')
    def _compute_production_count(self):
        for rec in self:
            rec.production_count = len(rec.production_order_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Mới')) == _('Mới'):
                company_id = vals.get('company_id') or self.env.company.id
                company = self.env['res.company'].browse(company_id)
                prefix = company.x_wood_prefix or 'QTP'
                
                seq = self.env['ir.sequence'].with_company(company).next_by_code('dl.wood.sale.order') or ''
                vals['name'] = f"{prefix}{seq}"
        return super().create(vals_list)

    def action_confirm(self):
        """Xác nhận đơn đặt hàng."""
        self.ensure_one()
        self.state = 'confirmed'

    def action_done(self):
        """Đánh dấu hoàn thành."""
        self.ensure_one()
        self.state = 'done'

    def action_cancel(self):
        """Hủy đơn đặt hàng."""
        self.ensure_one()
        self.state = 'cancelled'

    def action_draft(self):
        """Về trạng thái dự thảo."""
        self.ensure_one()
        self.state = 'draft'

    def action_view_productions(self):
        """Mở danh sách lệnh sản xuất của đơn hàng này."""
        self.ensure_one()
        return {
            'name': _('Lệnh sản xuất - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'dl.wood.production.order',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'default_sale_order_id': self.id, 'default_partner_id': self.partner_id.id},
        }


class DlWoodProductionOrder(models.Model):
    """Lệnh sản xuất - sản xuất một mặt hàng và tiêu hao nguyên vật liệu."""
    _name = 'dl.wood.production.order'
    _description = 'Lệnh sản xuất gỗ'
    _order = 'date_planned desc, name desc'

    name = fields.Char(
        string='Mã lệnh SX', required=True, copy=False,
        default=lambda self: _('Mới'), index=True
    )
    sale_order_id = fields.Many2one(
        'dl.wood.sale.order', string='Đơn đặt hàng', ondelete='cascade', index=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Công ty',
        related='sale_order_id.company_id',
        store=True,
        index=True
    )
    partner_id = fields.Many2one(
        'res.partner', related='sale_order_id.partner_id',
        string='Khách hàng', store=True, index=True
    )
    product_id = fields.Many2one(
        'product.product', string='Sản phẩm sản xuất', required=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), ('type', 'in', ['consu', 'product'])]"
    )
    qty_planned = fields.Float(string='Số lượng kế hoạch', digits=(16, 2), default=1.0)
    qty_done = fields.Float(string='Số lượng thực tế', digits=(16, 2))
    uom_id = fields.Many2one(
        'uom.uom', related='product_id.uom_id', string='Đơn vị tính', readonly=True
    )
    date_planned = fields.Date(string='Ngày dự kiến', default=fields.Date.context_today)
    date_done = fields.Date(string='Ngày hoàn thành')
    x_woodpro_id = fields.Char(string='ID WoodPro', index=True)
    note = fields.Text(string='Ghi chú')
    line_ids = fields.One2many(
        'dl.wood.production.line', 'production_order_id',
        string='Tiêu hao nguyên vật liệu'
    )
    total_volume_planned = fields.Float(
        string='Tổng KL kế hoạch (m³)', compute='_compute_total_volume', digits=(16, 2), store=True
    )
    total_volume_actual = fields.Float(
        string='Tổng KL thực tế (m³)', compute='_compute_total_volume', digits=(16, 2), store=True
    )
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('in_progress', 'Đang sản xuất'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Đã hủy'),
    ], string='Trạng thái', default='draft', index=True)

    @api.depends('line_ids.volume_planned', 'line_ids.volume_actual')
    def _compute_total_volume(self):
        for rec in self:
            rec.total_volume_planned = sum(rec.line_ids.mapped('volume_planned'))
            rec.total_volume_actual = sum(rec.line_ids.mapped('volume_actual'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Mới')) == _('Mới'):
                company_id = vals.get('company_id')
                if not company_id and vals.get('sale_order_id'):
                    sale_order = self.env['dl.wood.sale.order'].browse(vals['sale_order_id'])
                    company_id = sale_order.company_id.id
                
                company_id = company_id or self.env.company.id
                company = self.env['res.company'].browse(company_id)
                prefix = company.x_wood_prefix or 'QTP'
                
                seq = self.env['ir.sequence'].with_company(company).next_by_code('dl.wood.production.order') or ''
                vals['name'] = f"{prefix}{seq}"
        return super().create(vals_list)

    def action_start(self):
        """Bắt đầu sản xuất."""
        self.ensure_one()
        self.state = 'in_progress'

    def action_done(self):
        """Hoàn thành lệnh sản xuất và trừ lùi nguyên liệu."""
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_('Vui lòng nhập chi tiết tiêu hao nguyên vật liệu trước khi hoàn thành.'))
        self._action_deduct_materials()
        self.date_done = fields.Date.today()
        self.state = 'done'

    def action_cancel(self):
        """Hủy lệnh sản xuất (không hoàn lại nguyên liệu nếu đã done)."""
        self.ensure_one()
        if self.state == 'done':
            raise UserError(_('Không thể hủy lệnh sản xuất đã hoàn thành. Vui lòng liên hệ quản trị viên.'))
        self.state = 'cancelled'

    def action_draft(self):
        """Về trạng thái dự thảo."""
        self.ensure_one()
        self.state = 'draft'

    def _action_deduct_materials(self, force=False):
        """Trừ khối lượng gỗ thực tế từ các hồ sơ gỗ liên quan"""
        for line in self.line_ids:
            if not line.dossier_id:
                continue
            
            vol = line.volume_actual
            dossier = line.dossier_id
            
            if not force and dossier.remaining_qty < vol:
                raise ValidationError(_(
                    'Hồ sơ gỗ "%s" không đủ tồn kho!\n'
                    'Tồn kho hiện tại: %.2f m³ — Cần trừ: %.2f m³'
                ) % (dossier.name, dossier.remaining_qty, vol))
            
            # Trừ số lượng tồn kho
            dossier.remaining_qty -= vol
            
            # Tạo bản ghi vào sổ cái (Ledger) để hiện trong tab Lịch sử biến động
            self.env['dl.dossier.ledger'].create({
                'dossier_id': dossier.id,
                'production_id': self.id,
                'actual_qty': -vol, # Số âm vì là xuất nguyên liệu
                'state': 'done',
                'date': fields.Datetime.now(),
            })


class DlWoodProductionLine(models.Model):
    """Chi tiết tiêu hao nguyên vật liệu của một lệnh sản xuất."""
    _name = 'dl.wood.production.line'
    _description = 'Chi tiết NVL tiêu hao lệnh sản xuất'

    production_order_id = fields.Many2one(
        'dl.wood.production.order', string='Lệnh sản xuất',
        ondelete='cascade', required=True, index=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Công ty',
        related='production_order_id.company_id',
        store=True,
        index=True
    )
    species_id = fields.Many2one('dl.wood.species', string='Loại gỗ', required=True)
    dossier_id = fields.Many2one(
        'dl.wood.dossier', string='Hồ sơ gỗ nguồn',
        domain="[('company_id', '=', company_id), ('species_lines_species_id', '=', species_id)]",
        help='Hồ sơ gỗ mà nguyên liệu được lấy từ đó để sản xuất.'
    )
    volume_planned = fields.Float(string='KL kế hoạch (m³)', digits=(16, 2))
    volume_actual = fields.Float(string='KL thực tế (m³)', digits=(16, 2))
    note = fields.Char(string='Ghi chú')
