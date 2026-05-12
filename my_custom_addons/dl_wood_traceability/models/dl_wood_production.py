import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class DlWoodSaleOrder(models.Model):
    _name = 'dl.wood.sale.order'
    _description = 'Đơn bán hàng gỗ'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_order desc, id desc'

    name = fields.Char(string='Số đơn hàng', required=True, copy=False, default=lambda self: _('Mới'))
    partner_id = fields.Many2one('res.partner', string='Khách hàng', required=True)
    date_order = fields.Date(string='Ngày đặt hàng', default=fields.Date.context_today)
    note = fields.Text(string='Ghi chú')
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('confirmed', 'Đã xác nhận'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Đã hủy'),
    ], string='Trạng thái', default='draft')
    
    x_invoice_code = fields.Char(string='Mã hóa đơn', index=True)
    x_woodpro_id = fields.Char(string='ID WoodPro', index=True)
    
    production_order_ids = fields.One2many('dl.wood.production.order', 'sale_order_id', string='Lệnh sản xuất')
    production_count = fields.Integer(string='Số LSX', compute='_compute_production_count')

    def _compute_production_count(self):
        for rec in self:
            rec.production_count = len(rec.production_order_ids)

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_view_productions(self):
        self.ensure_one()
        return {
            'name': _('Lệnh sản xuất'),
            'type': 'ir.actions.act_window',
            'res_model': 'dl.wood.production.order',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'default_sale_order_id': self.id},
        }

    def action_open_link_production_wizard(self):
        self.ensure_one()
        return {
            'name': _('Chọn lệnh sản xuất có sẵn'),
            'type': 'ir.actions.act_window',
            'res_model': 'dl.link.production.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_order_id': self.id}
        }

class DlWoodProductionOrder(models.Model):
    _name = 'dl.wood.production.order'
    _description = 'Lệnh sản xuất gỗ'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_planned desc, id desc'

    name = fields.Char(
        string='Mã lệnh SX', required=True, copy=False,
        default=lambda self: _('Mới'), index=True
    )
    sale_order_id = fields.Many2one(
        'dl.wood.sale.order', string='Đơn bán hàng', ondelete='set null', index=True
    )
    partner_id = fields.Many2one(
        'res.partner', string='Khách hàng', index=True,
        help="Khách hàng đặt hàng hoặc khách hàng dự kiến cho lệnh sản xuất này."
    )

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        if self.sale_order_id and self.sale_order_id.partner_id:
            self.partner_id = self.sale_order_id.partner_id
    
    # LSX giờ đây chứa danh sách sản phẩm
    product_line_ids = fields.One2many(
        'dl.wood.production.product.line', 'production_order_id',
        string='Danh sách sản phẩm thành phẩm'
    )
    
    date_planned = fields.Date(string='Ngày dự kiến', default=fields.Date.context_today)
    date_order = fields.Datetime(string='Ngày đặt hàng')
    date_done = fields.Date(string='Ngày hoàn thành')
    
    x_woodpro_id = fields.Char(string='ID WoodPro', index=True)
    note = fields.Text(string='Ghi chú')
    
    total_volume_planned = fields.Float(
        string='Tổng KL nguyên liệu kế hoạch (m³)', compute='_compute_total_volume', digits=(16, 2), store=True
    )
    total_volume_actual = fields.Float(
        string='Tổng KL nguyên liệu thực tế (m³)', compute='_compute_total_volume', digits=(16, 2), store=True
    )
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('in_progress', 'Đang sản xuất'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Đã hủy'),
    ], string='Trạng thái', default='draft', index=True)

    @api.depends('product_line_ids.material_line_ids.volume_planned', 'product_line_ids.material_line_ids.volume_actual')
    def _compute_total_volume(self):
        for rec in self:
            total_p = 0.0
            total_a = 0.0
            for p_line in rec.product_line_ids:
                total_p += sum(p_line.material_line_ids.mapped('volume_planned'))
                total_a += sum(p_line.material_line_ids.mapped('volume_actual'))
            rec.total_volume_planned = total_p
            rec.total_volume_actual = total_a

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Mới')) == _('Mới'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dl.wood.production.order') or _('Mới')
        return super().create(vals_list)

    def action_start(self):
        self.ensure_one()
        if not self.product_line_ids:
            raise ValidationError(_("Vui lòng thêm ít nhất một sản phẩm vào lệnh sản xuất."))
        self.state = 'in_progress'

    def action_done(self):
        self.ensure_one()
        # Thực hiện trừ kho nguyên liệu từ tất cả các dòng sản phẩm
        self._action_deduct_materials()
        self.state = 'done'
        self.date_done = fields.Date.today()

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_draft(self):
        self.write({'state': 'draft'})

    # Liên kết với các chuyến vận chuyển
    trip_ids = fields.One2many('dl.wood.production.trip', 'production_order_id', string='Lịch sử vận chuyển')

    def _action_deduct_materials(self, force=False):
        """Lặp qua tất cả các dòng sản phẩm và trừ kho Hồ sơ gỗ tương ứng thông qua Sổ cái"""
        affected_dossiers = self.env['dl.wood.dossier']
        for p_line in self.product_line_ids:
            for m_line in p_line.material_line_ids:
                if not m_line.dossier_id:
                    continue
                
                vol = m_line.volume_actual
                dossier = m_line.dossier_id
                affected_dossiers |= dossier
                
                if not force and dossier.remaining_qty < vol:
                    raise ValidationError(_(
                        'Thành phẩm: %s\nHồ sơ gỗ "%s" không đủ tồn kho!\n'
                        'Tồn hiện tại: %.2f m³ — Cần trừ: %.2f m³'
                    ) % (p_line.product_id.name, dossier.name, dossier.remaining_qty, vol))
                
                # Tạo sổ cái (remaining_qty và các trường tồn kho khác sẽ tự động cập nhật nhờ @api.depends)
                self.env['dl.dossier.ledger'].create({
                    'dossier_id': dossier.id,
                    'production_id': self.id,
                    'wood_sale_id': self.sale_order_id.id,
                    'qty_before': dossier.remaining_qty,
                    'actual_qty': -vol,
                    'qty_after': dossier.remaining_qty - vol,
                    'x_norm': m_line.x_norm,
                    'note': f"Sản xuất: {p_line.product_id.name} (Lệnh: {self.name})",
                    'state': 'done',
                    'date': self.date_order or fields.Datetime.now(),
                })
        
        # Cập nhật số lượng LSX cho các hồ sơ gỗ bị ảnh hưởng
        if affected_dossiers:
            affected_dossiers._compute_production_count()

class DlWoodProductionProductLine(models.Model):
    _name = 'dl.wood.production.product.line'
    _description = 'Dòng sản phẩm trong Lệnh sản xuất'

    production_order_id = fields.Many2one('dl.wood.production.order', string='Lệnh sản xuất', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Sản phẩm', required=True)
    uom_id = fields.Many2one('uom.uom', related='product_id.uom_id', string='ĐVT', readonly=True)
    
    qty_planned = fields.Float(string='SL kế hoạch', digits=(16, 2), compute='_compute_trip_quantities', store=True)
    qty_done = fields.Float(string='SL thực tế', digits=(16, 2), compute='_compute_trip_quantities', store=True)
    
    x_conversion_rate = fields.Float(string='Hệ số quy đổi', default=1.3)
    x_woodpro_id = fields.Char(string='ID WoodPro', index=True)
    
    @api.depends('production_order_id.trip_ids.quantity', 'production_order_id.trip_ids.product_id')
    def _compute_trip_quantities(self):
        """Tính tổng số lượng từ các chuyến vận chuyển thuộc về sản phẩm này"""
        for line in self:
            trips = line.production_order_id.trip_ids.filtered(lambda t: t.product_id == line.product_id)
            total = sum(trips.mapped('quantity'))
            line.qty_planned = total
            line.qty_done = total

    material_line_ids = fields.One2many(
        'dl.wood.production.line', 'product_line_id',
        string='Tiêu hao Hồ sơ gỗ'
    )

    @api.onchange('product_id', 'qty_planned', 'x_conversion_rate')
    def _onchange_product_id_load_norms(self):
        """Tự động nạp định mức từ sản phẩm khi thay đổi"""
        if not self.product_id or not self.qty_planned:
            return
            
        if self.production_order_id.state == 'draft':
            norms = self.product_id.product_tmpl_id.x_norm_ids
            if not norms:
                return
                
            new_lines = []
            for norm in norms:
                planned_vol = self.qty_planned * norm.norm_quantity * self.x_conversion_rate
                new_lines.append((0, 0, {
                    'species_id': norm.species_id.id,
                    'volume_planned': planned_vol,
                    'volume_actual': planned_vol,
                    'note': f'Định mức: {norm.norm_quantity} x Hệ số: {self.x_conversion_rate}'
                }))
            self.material_line_ids = new_lines

class DlWoodProductionLine(models.Model):
    _name = 'dl.wood.production.line'
    _description = 'Chi tiết tiêu hao nguyên liệu'

    product_line_id = fields.Many2one('dl.wood.production.product.line', string='Dòng sản phẩm', ondelete='cascade')
    production_order_id = fields.Many2one(related='product_line_id.production_order_id', store=True)
    
    species_id = fields.Many2one('dl.wood.species', string='Loại gỗ', required=True)
    dossier_id = fields.Many2one('dl.wood.dossier', string='Hồ sơ gỗ', index=True, domain=[('state', '!=', 'closed')])
    
    @api.constrains('dossier_id')
    def _check_dossier_state(self):
        for rec in self:
            if rec.dossier_id and rec.dossier_id.state == 'closed':
                raise ValidationError(_('Hồ sơ gỗ "%s" đã ĐÓNG, không thể sử dụng để sản xuất!') % rec.dossier_id.name)
    
    volume_planned = fields.Float(string='Khối lượng kế hoạch (m³)', digits=(16, 2))
    volume_actual = fields.Float(string='Khối lượng thực tế (m³)', digits=(16, 2))
    x_rate = fields.Float(string='Tỷ lệ (%)', digits=(16, 2))
    x_norm = fields.Float(string='Định mức', digits=(16, 2))
    note = fields.Char(string='Ghi chú')

    @api.onchange('dossier_id')
    def _onchange_dossier_id(self):
        if self.dossier_id:
            self.x_norm = self.dossier_id.x_default_norm
            self._onchange_calc_volume()

    @api.onchange('x_rate', 'x_norm', 'product_line_id.qty_planned')
    def _onchange_calc_volume(self):
        for rec in self:
            qty = rec.product_line_id.qty_planned or 0.0
            rec.volume_planned = qty * rec.x_norm * (rec.x_rate / 100.0)
            rec.volume_actual = rec.volume_planned

class DlWoodProductionTrip(models.Model):
    _name = 'dl.wood.production.trip'
    _description = 'Chuyến vận chuyển thành phẩm'
    _order = 'date_ship desc, id desc'

    production_order_id = fields.Many2one('dl.wood.production.order', string='Lệnh sản xuất', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Sản phẩm')
    
    manifest_num = fields.Char(string='Số bảng kê')
    quantity = fields.Float(string='Số lượng', digits=(16, 2))
    
    license_plate = fields.Char(string='Biển số xe')
    driver_name = fields.Char(string='Tài xế')
    date_ship = fields.Date(string='Ngày vận chuyển')
    
    note = fields.Char(string='Ghi chú')
    x_woodpro_id = fields.Char(string='ID WoodPro (Trip)', index=True)
