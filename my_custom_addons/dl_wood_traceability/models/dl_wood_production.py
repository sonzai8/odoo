# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


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
    x_select_production_id = fields.Many2one(
        'dl.wood.production.order',
        string='Chọn lệnh SX có sẵn',
        domain="[('sale_order_id', '=', False)]",
        help='Chọn một lệnh sản xuất đã tạo sẵn chưa gắn với đơn hàng nào.'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Công ty',
        compute='_compute_company_id',
        store=True,
        readonly=False,
        required=True,
        default=lambda self: self.env.company,
        index=True
    )
    partner_id = fields.Many2one(
        'res.partner', related='sale_order_id.partner_id',
        string='Khách hàng', store=True, index=True
    )
    product_id = fields.Many2one(
        'product.product', string='Sản phẩm sản xuất', required=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), ('is_wood_product', '=', True)]"
    )
    qty_planned = fields.Float(string='Số lượng kế hoạch', digits=(16, 2), default=1.0)
    qty_done = fields.Float(string='Số lượng thực tế', digits=(16, 2), default=1.0)
    x_co_yield = fields.Float(string='Khai CO mặc định', digits=(16, 2), default=1.3, help='Hệ số Khai CO mặc định dùng để điền tự động khi thêm các bộ hồ sơ.')
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
    x_total_ratio = fields.Float(
        string='Tổng định mức (%)', compute='_compute_total_volume', digits=(16, 2), store=True
    )
    x_remaining_ratio = fields.Float(
        string='Định mức còn thiếu (%)', compute='_compute_total_volume', digits=(16, 2), store=True
    )
    x_remaining_volume_planned = fields.Float(
        string='KL kế hoạch còn thiếu (m³)', compute='_compute_total_volume', digits=(16, 2), store=True
    )
    x_remaining_volume_actual = fields.Float(
        string='KL thực tế còn thiếu (m³)', compute='_compute_total_volume', digits=(16, 2), store=True
    )
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('in_progress', 'Đang sản xuất'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Đã hủy'),
    ], string='Trạng thái', default='draft', index=True)

    @api.depends('line_ids.volume_planned', 'line_ids.volume_actual', 'line_ids.x_ratio', 'qty_planned', 'qty_done', 'x_co_yield')
    def _compute_total_volume(self):
        for rec in self:
            total_vol_plan = sum(rec.line_ids.mapped('volume_planned'))
            total_vol_act = sum(rec.line_ids.mapped('volume_actual'))
            rec.total_volume_planned = round(total_vol_plan, 2)
            rec.total_volume_actual = round(total_vol_act, 2)

            total_ratio = sum(rec.line_ids.mapped('x_ratio'))
            rec.x_total_ratio = round(total_ratio, 2)
            
            remaining_ratio = max(0.0, 100.0 - total_ratio)
            rec.x_remaining_ratio = round(remaining_ratio, 2)
            
            total_vol_planned_needed = rec.qty_planned * rec.x_co_yield
            rec.x_remaining_volume_planned = round(max(0.0, total_vol_planned_needed - total_vol_plan), 2)
            
            total_vol_actual_needed = rec.qty_done * rec.x_co_yield
            rec.x_remaining_volume_actual = round(max(0.0, total_vol_actual_needed - total_vol_act), 2)

    @api.depends('sale_order_id.company_id')
    def _compute_company_id(self):
        for rec in self:
            if rec.sale_order_id:
                rec.company_id = rec.sale_order_id.company_id
            elif not rec.company_id:
                rec.company_id = self.env.company

    @api.onchange('qty_planned')
    def _onchange_qty_planned(self):
        for rec in self:
            if rec.qty_planned:
                rec.qty_done = rec.qty_planned

    @api.onchange('qty_planned', 'qty_done')
    def _onchange_production_quantities(self):
        for rec in self:
            for line in rec.line_ids:
                if line.x_ratio:
                    line.volume_planned = round((rec.qty_planned * line.x_co_yield) * (line.x_ratio / 100.0), 2)
                    line.volume_actual = round((rec.qty_done * line.x_co_yield) * (line.x_ratio / 100.0), 2)

    @api.onchange('x_co_yield')
    def _onchange_x_co_yield(self):
        for rec in self:
            for line in rec.line_ids:
                line.x_co_yield = rec.x_co_yield
                if line.x_ratio:
                    line.volume_planned = round((rec.qty_planned * line.x_co_yield) * (line.x_ratio / 100.0), 2)
                    line.volume_actual = round((rec.qty_done * line.x_co_yield) * (line.x_ratio / 100.0), 2)

    @api.constrains('line_ids', 'state')
    def _check_ratios_total(self):
        for rec in self:
            if rec.state in ('in_progress', 'done') and rec.line_ids:
                total_ratio = sum(rec.line_ids.mapped('x_ratio'))
                if abs(total_ratio - 100.0) > 0.01:
                    raise ValidationError(_('Tổng định mức (%%) tiêu hao nguyên vật liệu của các bộ hồ sơ gỗ phải bằng chính xác 100%% (Hiện tại là: %s%%).') % total_ratio)

    @api.onchange('x_select_production_id')
    def _onchange_x_select_production_id(self):
        for rec in self:
            if rec.x_select_production_id:
                prod = rec.x_select_production_id
                rec.product_id = prod.product_id
                rec.qty_planned = prod.qty_planned
                rec.qty_done = prod.qty_done
                rec.date_planned = prod.date_planned
                rec.x_co_yield = prod.x_co_yield
                rec.note = prod.note

    @api.model_create_multi
    def create(self, vals_list):
        new_vals_list = []
        existing_records_to_update = []
        
        for vals in vals_list:
            if vals.get('x_select_production_id'):
                existing_records_to_update.append((vals['x_select_production_id'], vals))
            else:
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
                new_vals_list.append(vals)
                
        records = super(DlWoodProductionOrder, self).create(new_vals_list)
        
        # Link existing production orders by writing sale_order_id!
        for prod_id, vals in existing_records_to_update:
            existing_prod = self.browse(prod_id)
            if existing_prod:
                existing_prod.write({
                    'sale_order_id': vals.get('sale_order_id'),
                    'x_select_production_id': prod_id,
                })
                records += existing_prod
                
        return records


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

    def action_previous_state(self):
        """Quay lại trạng thái trước đó."""
        self.ensure_one()
        if self.state == 'in_progress':
            # Từ Đang sản xuất quay về Dự thảo
            self.state = 'draft'
            _logger.info(f"Lệnh sản xuất {self.name} đã được chuyển về trạng thái Dự thảo.")
        elif self.state == 'done':
            # Từ Hoàn thành quay về Đang sản xuất
            # Hoàn trả lại số lượng nguyên vật liệu đã trừ của từng hồ sơ gỗ nguồn
            for line in self.line_ids:
                if line.dossier_id and line.volume_actual:
                    line.dossier_id.remaining_qty += line.volume_actual
                    _logger.info(f"Đã hoàn trả {line.volume_actual} m3 gỗ cho hồ sơ nguồn {line.dossier_id.name}")
            
            # Xóa các bản ghi biến động sổ cái (Ledger) tương ứng
            ledgers = self.env['dl.dossier.ledger'].search([('production_id', '=', self.id)])
            if ledgers:
                ledgers.unlink()
                _logger.info(f"Đã xóa {len(ledgers)} dòng biến động sổ cái liên quan.")
                
            self.date_done = False
            self.state = 'in_progress'
            _logger.info(f"Lệnh sản xuất {self.name} đã được hoàn trả nguyên vật liệu và chuyển về Đang sản xuất.")
        else:
            raise UserError(_('Không hỗ trợ quay lại trạng thái trước từ trạng thái hiện tại.'))

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

    def write(self, vals):
        for rec in self:
            if rec.state in ('done', 'cancelled'):
                allowed_fields = {'note', 'date_done', 'state'}
                modified_fields = set(vals.keys())
                if not modified_fields.issubset(allowed_fields):
                    raise UserError(_('Không thể chỉnh sửa các thông tin nghiệp vụ của Lệnh sản xuất đã Hoàn thành hoặc Hủy.'))
        return super(DlWoodProductionOrder, self).write(vals)

    def unlink(self):
        for rec in self:
            if rec.state in ('done', 'cancelled'):
                raise UserError(_('Không thể xóa Lệnh sản xuất đã Hoàn thành hoặc Hủy.'))
        
        records_to_unlink = self.env['dl.wood.production.order']
        for rec in self:
            if rec.x_select_production_id:
                rec.write({'sale_order_id': False})
            else:
                records_to_unlink += rec
        return super(DlWoodProductionOrder, records_to_unlink).unlink()


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
        domain="[('company_id', '=', company_id), ('state', '!=', 'cancelled')]",
        help='Hồ sơ gỗ mà nguyên liệu được lấy từ đó để sản xuất.'
    )
    x_available_species_ids = fields.Many2many(
        'dl.wood.species',
        compute='_compute_x_available_species_ids',
        string='Loài gỗ khả dụng'
    )
    x_ratio = fields.Float(string='Định mức %', digits=(16, 2), default=0.0)
    x_co_yield = fields.Float(string='Khai CO', digits=(16, 2), default=1.3, help='Hệ số hao hụt nguyên vật liệu/thành phẩm của bộ hồ sơ này.')
    volume_planned = fields.Float(string='KL kế hoạch (m³)', digits=(16, 2))
    volume_actual = fields.Float(string='KL thực tế (m³)', digits=(16, 2))
    note = fields.Char(string='Ghi chú')

    @api.depends('dossier_id')
    def _compute_x_available_species_ids(self):
        for line in self:
            if line.dossier_id:
                species_ids = line.dossier_id.line_ids.mapped('species_id').ids
                line.x_available_species_ids = [(6, 0, species_ids)]
            else:
                line.x_available_species_ids = [(6, 0, [])]

    @api.onchange('dossier_id')
    def _onchange_dossier_id(self):
        if self.dossier_id:
            species = self.dossier_id.line_ids.mapped('species_id')
            if len(species) == 1:
                self.species_id = species[0]
            else:
                self.species_id = False
            
            order = self.production_order_id
            if order:
                self.x_co_yield = order.x_co_yield
                
                # Tính định mức tự động thông minh dựa trên khối lượng còn lại của hồ sơ gỗ
                if order.qty_planned > 0:
                    total_volume_needed = order.qty_planned * self.x_co_yield
                    if total_volume_needed > 0:
                        other_lines = order.line_ids - self
                        other_lines_ratio_sum = sum(other_lines.mapped('x_ratio'))
                        remaining_ratio_needed = max(0.0, 100.0 - other_lines_ratio_sum)
                        
                        raw_volume_needed = total_volume_needed * (remaining_ratio_needed / 100.0)
                        # Khối lượng khả dụng còn lại của bộ hồ sơ gỗ
                        dossier_qty_avail = max(0.0, self.dossier_id.qty_available)
                        
                        if dossier_qty_avail >= raw_volume_needed:
                            self.x_ratio = round(remaining_ratio_needed, 2)
                        else:
                            allocated_ratio = (dossier_qty_avail / total_volume_needed) * 100.0
                            self.x_ratio = round(allocated_ratio, 2)
                            
                        # Tính toán KL planned/actual của dòng
                        self.volume_planned = round((order.qty_planned * self.x_co_yield) * (self.x_ratio / 100.0), 2)
                        self.volume_actual = round((order.qty_done * self.x_co_yield) * (self.x_ratio / 100.0), 2)
        else:
            self.species_id = False

    @api.onchange('x_ratio', 'x_co_yield')
    def _onchange_ratio_and_co(self):
        for line in self:
            if line.x_ratio:
                order = line.production_order_id
                line.volume_planned = round((order.qty_planned * line.x_co_yield) * (line.x_ratio / 100.0), 2)
                line.volume_actual = round((order.qty_done * line.x_co_yield) * (line.x_ratio / 100.0), 2)

    @api.onchange('volume_planned')
    def _onchange_volume_planned(self):
        if self.volume_planned:
            self.volume_actual = self.volume_planned

    def write(self, vals):
        for line in self:
            if line.production_order_id.state in ('done', 'cancelled'):
                raise UserError(_('Không thể chỉnh sửa tiêu hao nguyên vật liệu của Lệnh sản xuất đã Hoàn thành hoặc Hủy.'))
        return super(DlWoodProductionLine, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('production_order_id'):
                order = self.env['dl.wood.production.order'].browse(vals['production_order_id'])
                if order.state in ('done', 'cancelled'):
                    raise UserError(_('Không thể thêm tiêu hao nguyên vật liệu cho Lệnh sản xuất đã Hoàn thành hoặc Hủy.'))
        return super(DlWoodProductionLine, self).create(vals_list)

    def unlink(self):
        for line in self:
            if line.production_order_id.state in ('done', 'cancelled'):
                raise UserError(_('Không thể xóa tiêu hao nguyên vật liệu của Lệnh sản xuất đã Hoàn thành hoặc Hủy.'))
        return super(DlWoodProductionLine, self).unlink()
