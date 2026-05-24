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
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), ('is_wood_product', '=', True), ('sale_ok', '=', True), ('active', '=', True)]"
    )
    qty_planned = fields.Float(string='Số lượng kế hoạch', digits=(16, 2), default=1.0)
    qty_done = fields.Float(string='Số lượng thực tế', digits=(16, 2), default=1.0)
    x_co_yield = fields.Float(string='Khai CO mặc định', digits=(16, 2), default=1.3, help='Hệ số Khai CO mặc định dùng để điền tự động khi thêm các bộ hồ sơ.')
    uom_id = fields.Many2one(
        'uom.uom', related='product_id.uom_id', string='Đơn vị tính Odoo', readonly=True
    )
    x_product_unit_label = fields.Char(
        string='Đơn vị tính',
        compute='_compute_x_product_unit_label',
        store=False
    )
    date_planned = fields.Date(string='Ngày dự kiến', default=fields.Date.context_today)
    date_done = fields.Date(string='Ngày hoàn thành')
    x_woodpro_id = fields.Char(string='ID WoodPro', index=True)
    note = fields.Text(string='Ghi chú')
    line_ids = fields.One2many(
        'dl.wood.production.line', 'production_order_id',
        string='Tiêu hao nguyên vật liệu'
    )
    peeling_line_ids = fields.One2many(
        'dl.wood.peeling.production.line', 'production_order_id',
        string='Tiêu hao ván bóc'
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

    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Tiền tệ',
        readonly=True
    )
    x_total_wood_cost = fields.Float(
        string='Tổng tiền gỗ (VND)',
        compute='_compute_production_costs',
        store=True,
        digits=(16, 2)
    )
    x_avg_production_price = fields.Float(
        string='Giá SX trung bình (VND/m³ thành phẩm)',
        compute='_compute_production_costs',
        store=True,
        digits=(16, 2)
    )
    x_avg_production_price_explanation = fields.Html(
        string='Giải thích chi tiết chi phí',
        compute='_compute_production_costs',
        store=True
    )

    # ── Hiển thị quy đổi số lượng → m³ thành phẩm ───────────────────────────
    x_uom_is_piece = fields.Boolean(
        string='Đơn vị là Tấm',
        compute='_compute_x_volume_conversion',
        store=False,
        help='True nếu đơn vị tính của sản phẩm có chứa từ "tấm" — dùng để hiện thị thông tin quy đổi.'
    )
    x_qty_planned_m3 = fields.Float(
        string='Số lượng kế hoạch (m³)',
        compute='_compute_x_volume_conversion',
        store=False,
        digits=(16, 2),
        help='Quy đổi số lượng kế hoạch sang m³ dựa trên x_volume_m3 của sản phẩm.'
    )
    x_qty_done_m3 = fields.Float(
        string='Số lượng thực tế (m³)',
        compute='_compute_x_volume_conversion',
        store=False,
        digits=(16, 2),
        help='Quy đổi số lượng thực tế sang m³ dựa trên x_volume_m3 của sản phẩm.'
    )

    @api.depends('product_id', 'product_id.uom_id')
    def _compute_x_product_unit_label(self):
        for rec in self:
            label = ''
            if rec.product_id:
                x_unit_val = getattr(rec.product_id, 'x_unit', False)
                if x_unit_val == 'sheet':
                    label = 'Tấm'
                elif x_unit_val == 'm3':
                    label = 'm³'
                else:
                    label = rec.product_id.uom_id.name or ''
            rec.x_product_unit_label = label

    @api.constrains('product_id')
    def _check_product_id(self):
        for rec in self:
            if rec.product_id:
                is_wood = rec.product_id.is_wood_product or getattr(rec.product_id, 'x_is_wood_product', False)
                if not is_wood:
                    raise ValidationError(_("Chỉ được phép chọn sản phẩm sản xuất ngành gỗ cho lệnh sản xuất! Vui lòng chọn sản phẩm khác hoặc tạo mới sản phẩm gỗ từ menu Danh mục sản phẩm gỗ."))

    def _get_vol_per_unit(self):
        """Helper để lấy thể tích m³ trên mỗi đơn vị (Tấm/m³...) của sản phẩm."""
        self.ensure_one()
        if not self.product_id:
            return 1.0

        x_unit_val = getattr(self.product_id, 'x_unit', '')
        
        # 1. Nếu x_unit = m3 thì không cần quy đổi, khối lượng nhập vào chính là khối lượng lệnh sản xuất
        if x_unit_val == 'm3':
            return 1.0

        # 2. Nếu x_unit = sheet thì quy đổi từ tấm sang m3
        if x_unit_val == 'sheet':
            vol_per_unit = self.product_id.x_volume_m3
            if not vol_per_unit:
                p = self.product_id
                if p.x_length and p.x_width and p.x_thickness:
                    area = (p.x_length * p.x_width) / 1_000_000.0  # mm² → m²
                    vol_per_unit = (area * p.x_thickness) / 1_000.0  # mm → m
            return vol_per_unit or 1.0

        # 3. Fallback dự phòng nếu x_unit trống hoặc có giá trị khác
        uom_name = self.product_id.uom_id.name or ''
        if any(x in uom_name.lower() for x in ['m³', 'm3', 'mét khối', 'met khoi']):
            return 1.0

        vol_per_unit = self.product_id.x_volume_m3
        if not vol_per_unit:
            p = self.product_id
            if p.x_length and p.x_width and p.x_thickness:
                area = (p.x_length * p.x_width) / 1_000_000.0  # mm² → m²
                vol_per_unit = (area * p.x_thickness) / 1_000.0  # mm → m
        return vol_per_unit or 1.0

    @api.depends('qty_planned', 'qty_done', 'product_id', 'product_id.uom_id',
                 'product_id.x_volume_m3', 'product_id.x_length',
                 'product_id.x_width', 'product_id.x_thickness')
    def _compute_x_volume_conversion(self):
        """Tính quy đổi số lượng tấm → m³ và detect đơn vị là Tấm."""
        for rec in self:
            uom_name = (rec.product_id.uom_id.name or '').strip().lower()
            x_unit_val = getattr(rec.product_id, 'x_unit', '')
            rec.x_uom_is_piece = 'tấm' in uom_name or 'tam' in uom_name or x_unit_val == 'sheet'

            vol_per_unit = rec._get_vol_per_unit()
            rec.x_qty_planned_m3 = round(rec.qty_planned * vol_per_unit, 2)
            rec.x_qty_done_m3    = round(rec.qty_done    * vol_per_unit, 2)

    @api.depends('line_ids.x_subtotal_cost', 'line_ids.volume_planned', 'line_ids.volume_actual', 'line_ids.x_price_unit', 
                 'peeling_line_ids.x_subtotal_cost', 'peeling_line_ids.volume_planned', 'peeling_line_ids.volume_actual', 'peeling_line_ids.x_price_unit',
                 'qty_done', 'qty_planned', 'product_id.x_volume_m3', 'product_id.uom_id.name', 'state')
    def _compute_production_costs(self):
        for rec in self:
            total_wood_cost = sum(rec.line_ids.mapped('x_subtotal_cost'))
            total_peeling_cost = sum(rec.peeling_line_ids.mapped('x_subtotal_cost'))
            total_cost = total_wood_cost + total_peeling_cost
            rec.x_total_wood_cost = round(total_cost, 2)

            qty = rec.qty_done if rec.state in ('in_progress', 'done') else rec.qty_planned
            if not qty:
                qty = rec.qty_planned or 1.0

            vol_per_unit = rec._get_vol_per_unit()

            total_finished_volume = qty * vol_per_unit
            if total_finished_volume > 0:
                rec.x_avg_production_price = round(total_cost / total_finished_volume, 2)
            else:
                rec.x_avg_production_price = round(total_cost / qty, 2) if qty > 0 else 0.0

            # Xây dựng phần giải thích chi tiết - hiển thị công thức đầy đủ theo yêu cầu:
            # ( 30M3 x 1.900.000 + 50M3 x 1.800.000 ) / ( 30M3 + 50M3 ) = XX
            explanation_html = ""
            active_lines = rec.line_ids.filtered(lambda l: (l.volume_planned if rec.state == 'draft' else l.volume_actual) > 0)

            if not active_lines:
                explanation_html = """
                    <div style="font-size: 0.85rem; color: #7f8c8d; padding: 10px; background-color: #f8f9fa; border-radius: 4px; border: 1px dashed #dee2e6; margin-top: 15px;">
                        <i class="fa fa-info-circle" style="color: #6c757d; margin-right: 5px;"></i>
                        Chưa có dòng tiêu hao nguyên vật liệu nào có khối lượng lớn hơn 0 để hiển thị chi tiết phép tính.
                    </div>
                """
            else:
                # Thu thập dữ liệu từng dòng nguyên liệu
                parts_numerator = []   # ["30,00 m³ x 1.900.000", "50,00 m³ x 1.800.000"]
                parts_vol_denom = []   # ["30,00 m³", "50,00 m³"]
                total_vol_raw = 0.0

                for line in active_lines:
                    v = line.volume_planned if rec.state == 'draft' else line.volume_actual
                    total_vol_raw += v
                    fmt_price = f"{int(line.x_price_unit):,}".replace(",", ".")
                    fmt_vol   = f"{v:,.2f}"
                    parts_numerator.append(f"{fmt_vol} M³ x {fmt_price}")
                    parts_vol_denom.append(f"{fmt_vol} M³")

                # ── Giá trung bình gỗ nguyên liệu (cách 1) ──────────────────────────────
                avg_raw_price = round(total_cost / total_vol_raw, 2) if total_vol_raw > 0 else 0.0
                fmt_avg_raw   = f"{int(avg_raw_price):,}".replace(",", ".")
                fmt_total_cost = f"{int(total_cost):,}".replace(",", ".")
                fmt_vol_raw   = f"{total_vol_raw:,.2f}"

                # Ví dụ: ( 30,00 M³ x 1.900.000 + 50,00 M³ x 1.800.000 ) / ( 30,00 M³ + 50,00 M³ ) = 1.843.750 VND/m³ gỗ NL
                raw_numerator  = " + ".join(parts_numerator)
                raw_denominator = " + ".join(parts_vol_denom)
                raw_formula_full = (
                    f"( {raw_numerator} ) / ( {raw_denominator} )"
                    f" = <strong>{fmt_avg_raw} VND / m³ gỗ nguyên liệu</strong>"
                )
                # Dòng rút gọn: tổng tiền / tổng m³ = kết quả
                raw_simplified = (
                    f"{fmt_total_cost} / {fmt_vol_raw} m³"
                    f" = <strong>{fmt_avg_raw} VND / m³ gỗ nguyên liệu</strong>"
                )

                # ── Chi phí gỗ trên mỗi m³ thành phẩm (cách 2) ─────────────────────────
                fmt_avg_prod = f"{int(rec.x_avg_production_price):,}".replace(",", ".")

                if total_finished_volume > 0:
                    fmt_fin_vol  = f"{total_finished_volume:,.3f}"
                    unit_label   = "m³ thành phẩm"
                    # Ví dụ: ( 30,00 M³ x 1.900.000 + 50,00 M³ x 1.800.000 ) / 2,400 m³ thành phẩm = XX VND/m³
                    fin_formula_full = (
                        f"( {raw_numerator} ) / {fmt_fin_vol} m³ thành phẩm"
                        f" = <strong>{fmt_avg_prod} VND / m³ thành phẩm</strong>"
                    )
                    fin_simplified = (
                        f"{fmt_total_cost} / {fmt_fin_vol} m³ thành phẩm"
                        f" = <strong>{fmt_avg_prod} VND / m³ thành phẩm</strong>"
                    )
                    note_finished = (
                        f"* Thể tích thành phẩm = {qty:,.0f} {rec.product_id.uom_id.name or 'đơn vị'}"
                        f" × {vol_per_unit:,.5f} m³/đơn vị = {fmt_fin_vol} m³"
                    )
                else:
                    fmt_qty = f"{qty:,.0f}"
                    fin_formula_full = (
                        f"( {raw_numerator} ) / {fmt_qty} đơn vị"
                        f" = <strong>{fmt_avg_prod} VND / đơn vị</strong>"
                    )
                    fin_simplified = (
                        f"{fmt_total_cost} / {fmt_qty} đơn vị"
                        f" = <strong>{fmt_avg_prod} VND / đơn vị</strong>"
                    )
                    note_finished = f"* Chưa có thể tích m³/đơn vị — tính theo số lượng đơn vị."

                state_label = "Dự thảo – Ước tính" if rec.state == 'draft' else "Thực tế sản xuất"

                explanation_html = f"""
                    <div style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 0.85rem; color: #444; line-height: 1.7; margin-top: 0px; border-top: 1px dashed #ced4da; padding-top: 12px;">

                        <div style="font-weight: bold; color: #2c3e50; margin-bottom: 10px; display: flex; align-items: center; font-size: 0.9rem;">
                            <i class="fa fa-calculator" style="color: #00878a; margin-right: 6px; font-size: 1rem;"></i>
                            Chi tiết tính toán chi phí ({state_label}):
                        </div>

                        <!-- MỤC 1: Giá NL trung bình / m³ gỗ nguyên liệu -->
                        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; margin-bottom: 10px;">
                            <div style="font-weight: 600; color: #3182ce; margin-bottom: 8px; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.03em;">
                                <i class="fa fa-arrow-right" style="font-size: 0.75rem; margin-right: 4px;"></i>
                                1. Giá gỗ nguyên liệu trung bình đầu vào:
                            </div>
                            <!-- Công thức đầy đủ -->
                            <div style="font-family: Consolas, 'Courier New', monospace; background: #fff; padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 0.82rem; color: #2d3748; overflow-x: auto; white-space: nowrap; margin-bottom: 6px;">
                                {raw_formula_full}
                            </div>
                            <!-- Dòng rút gọn -->
                            <div style="font-family: Consolas, 'Courier New', monospace; background: #edf2f7; padding: 6px 12px; border-radius: 4px; font-size: 0.82rem; color: #4a5568; overflow-x: auto; white-space: nowrap;">
                                ≡&nbsp; {raw_simplified}
                            </div>
                        </div>

                        <!-- MỤC 2: TẠM ẨN — xem code Python để bật lại -->

                    </div>
                """
            rec.x_avg_production_price_explanation = explanation_html

    @api.depends('line_ids.volume_planned', 'line_ids.volume_actual', 'line_ids.x_ratio', 
                 'peeling_line_ids.volume_planned', 'peeling_line_ids.volume_actual', 'peeling_line_ids.x_ratio',
                 'qty_planned', 'qty_done', 'x_co_yield')
    def _compute_total_volume(self):
        for rec in self:
            total_vol_plan = sum(rec.line_ids.mapped('volume_planned')) + sum(rec.peeling_line_ids.mapped('volume_planned'))
            total_vol_act = sum(rec.line_ids.mapped('volume_actual')) + sum(rec.peeling_line_ids.mapped('volume_actual'))
            rec.total_volume_planned = round(total_vol_plan, 2)
            rec.total_volume_actual = round(total_vol_act, 2)

            total_ratio = sum(rec.line_ids.mapped('x_ratio')) + sum(rec.peeling_line_ids.mapped('x_ratio'))
            rec.x_total_ratio = round(total_ratio, 2)
            
            remaining_ratio = max(0.0, 100.0 - total_ratio)
            rec.x_remaining_ratio = round(remaining_ratio, 2)
            
            vol_per_unit = rec._get_vol_per_unit()
            total_vol_planned_needed = (rec.qty_planned * vol_per_unit) * rec.x_co_yield
            rec.x_remaining_volume_planned = round(max(0.0, total_vol_planned_needed - total_vol_plan), 2)
            
            total_vol_actual_needed = (rec.qty_done * vol_per_unit) * rec.x_co_yield
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
            vol_per_unit = rec._get_vol_per_unit()
            for line in rec.line_ids:
                if line.x_ratio:
                    vol_planned = round(((rec.qty_planned * vol_per_unit) * line.x_co_yield) * (line.x_ratio / 100.0), 2)
                    vol_actual = round(((rec.qty_done * vol_per_unit) * line.x_co_yield) * (line.x_ratio / 100.0), 2)
                    if line.dossier_id:
                        avail_qty = 0.0
                        if line.x_dossier_line_ids:
                            avail_qty = sum(line.x_dossier_line_ids.mapped('x_qty_available'))
                        elif line.species_id:
                            avail_qty = sum(line.dossier_id.line_ids.filtered(lambda l: l.species_id == line.species_id).mapped('x_qty_available'))
                        else:
                            avail_qty = line.dossier_id.remaining_qty
                        
                        if vol_planned > avail_qty:
                            total_needed = (rec.qty_planned * vol_per_unit) * line.x_co_yield
                            if total_needed > 0:
                                line.x_ratio = round((avail_qty / total_needed) * 100.0, 2)
                                vol_planned = round(total_needed * (line.x_ratio / 100.0), 2)
                                vol_actual = round(((rec.qty_done * vol_per_unit) * line.x_co_yield) * (line.x_ratio / 100.0), 2)
                        
                        vol_planned = min(vol_planned, avail_qty)
                        vol_actual = min(vol_actual, avail_qty)
                    line.volume_planned = vol_planned
                    line.volume_actual = vol_actual

            for p_line in rec.peeling_line_ids:
                if p_line.x_ratio:
                    vol_planned = round(((rec.qty_planned * vol_per_unit) * p_line.x_co_yield) * (p_line.x_ratio / 100.0), 2)
                    vol_actual = round(((rec.qty_done * vol_per_unit) * p_line.x_co_yield) * (p_line.x_ratio / 100.0), 2)
                    if p_line.peeling_dossier_id:
                        avail_qty = 0.0
                        if p_line.peeling_dossier_line_ids:
                            avail_qty = sum(p_line.peeling_dossier_line_ids.mapped('qty_available'))
                        elif p_line.peeling_type_id:
                            lines = p_line.peeling_dossier_id.line_ids.filtered(lambda l: l.peeling_type_id == p_line.peeling_type_id)
                            avail_qty = sum(lines.mapped('qty_available'))
                        
                        if vol_planned > avail_qty:
                            total_needed = (rec.qty_planned * vol_per_unit) * p_line.x_co_yield
                            if total_needed > 0:
                                p_line.x_ratio = round((avail_qty / total_needed) * 100.0, 2)
                                vol_planned = round(total_needed * (p_line.x_ratio / 100.0), 2)
                                vol_actual = round(((rec.qty_done * vol_per_unit) * p_line.x_co_yield) * (p_line.x_ratio / 100.0), 2)
                        
                        vol_planned = min(vol_planned, avail_qty)
                        vol_actual = min(vol_actual, avail_qty)
                    p_line.volume_planned = vol_planned
                    p_line.volume_actual = vol_actual

    @api.onchange('x_co_yield')
    def _onchange_x_co_yield(self):
        for rec in self:
            vol_per_unit = rec._get_vol_per_unit()
            for line in rec.line_ids:
                line.x_co_yield = rec.x_co_yield
                if line.x_ratio:
                    vol_planned = round(((rec.qty_planned * vol_per_unit) * line.x_co_yield) * (line.x_ratio / 100.0), 2)
                    vol_actual = round(((rec.qty_done * vol_per_unit) * line.x_co_yield) * (line.x_ratio / 100.0), 2)
                    if line.dossier_id:
                        avail_qty = 0.0
                        if line.species_id:
                            avail_qty = sum(line.dossier_id.line_ids.filtered(lambda l: l.species_id == line.species_id).mapped('x_qty_available'))
                        else:
                            avail_qty = line.dossier_id.remaining_qty
                        vol_planned = min(vol_planned, avail_qty)
                        vol_actual = min(vol_actual, avail_qty)
                    line.volume_planned = vol_planned
                    line.volume_actual = vol_actual

            for p_line in rec.peeling_line_ids:
                p_line.x_co_yield = rec.x_co_yield
                if p_line.x_ratio:
                    vol_planned = round(((rec.qty_planned * vol_per_unit) * p_line.x_co_yield) * (p_line.x_ratio / 100.0), 2)
                    vol_actual = round(((rec.qty_done * vol_per_unit) * p_line.x_co_yield) * (p_line.x_ratio / 100.0), 2)
                    if p_line.peeling_dossier_id:
                        avail_qty = 0.0
                        if p_line.peeling_type_id:
                            lines = p_line.peeling_dossier_line_ids or p_line.peeling_dossier_id.line_ids.filtered(lambda l: l.peeling_type_id == p_line.peeling_type_id)
                            avail_qty = sum(lines.mapped('qty_available'))
                        vol_planned = min(vol_planned, avail_qty)
                        vol_actual = min(vol_actual, avail_qty)
                    p_line.volume_planned = vol_planned
                    p_line.volume_actual = vol_actual

    @api.constrains('line_ids', 'peeling_line_ids', 'state')
    def _check_ratios_total(self):
        for rec in self:
            # Chỉ bắt buộc tổng định mức bằng 100% khi Lệnh sản xuất ở trạng thái Hoàn thành (done).
            # Cho phép trạng thái nháp (draft) hoặc đang sản xuất (in_progress) được lưu với định mức khác 100%
            # để người dùng có thể dễ dàng điều chỉnh dữ liệu hoặc quay lại trạng thái trước đó (Rollback).
            if rec.state == 'done' and (rec.line_ids or rec.peeling_line_ids):
                total_ratio = sum(rec.line_ids.mapped('x_ratio')) + sum(rec.peeling_line_ids.mapped('x_ratio'))
                if abs(total_ratio - 100.0) > 0.01:
                    raise ValidationError(_('Tổng định mức (%%) tiêu hao nguyên vật liệu của các bộ hồ sơ gỗ/ván bóc phải bằng chính xác 100%% (Hiện tại là: %s%%).') % total_ratio)

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
        """Bắt đầu sản xuất và kiểm tra tồn kho nguyên liệu kế hoạch."""
        self.ensure_one()
        if not self.line_ids and not self.peeling_line_ids:
            raise UserError(_('Vui lòng nhập chi tiết tiêu hao nguyên vật liệu trước khi bắt đầu sản xuất.'))
        
        # Kiểm tra tồn kho khả dụng cho các dòng nguyên liệu dựa trên volume_planned
        line_avail_cache = {}
        for line in self.line_ids:
            if not line.dossier_id or not line.species_id:
                continue
            
            vol_needed = line.volume_planned
            # Lấy các dòng chi tiết được chọn hoặc tất cả dòng cùng loài gỗ
            lines_to_use = line.x_dossier_line_ids or line.dossier_id.line_ids.filtered(lambda dl: dl.species_id == line.species_id)
            if not lines_to_use:
                raise ValidationError(_(
                    'Hồ sơ gỗ "%s" không có loài gỗ "%s"!'
                ) % (line.dossier_id.name, line.species_id.name))
                
            # Sắp xếp theo chiều cao (dài) giảm dần, sau đó là ID tăng dần
            def sort_key(dl):
                origin_id = dl._origin.id if dl._origin else False
                val_id = origin_id if isinstance(origin_id, int) else (dl.id if isinstance(dl.id, int) else id(dl.id))
                return (dl.height, -val_id)
            sorted_lines = lines_to_use.sorted(key=sort_key, reverse=True)
            
            vol_remaining = vol_needed
            for dossier_line in sorted_lines:
                if vol_remaining <= 0:
                    break
                if dossier_line.id not in line_avail_cache:
                    line_avail_cache[dossier_line.id] = dossier_line.x_qty_available
                
                avail = line_avail_cache[dossier_line.id]
                if avail <= 0:
                    continue
                    
                if avail >= vol_remaining:
                    line_avail_cache[dossier_line.id] -= vol_remaining
                    vol_remaining = 0.0
                else:
                    line_avail_cache[dossier_line.id] = 0.0
                    vol_remaining -= avail
            
            if vol_remaining > 0:
                diff = vol_remaining
                if diff <= 0.05:
                    # Chấp nhận sai số làm tròn nhỏ
                    line.volume_planned = max(0.0, line.volume_planned - diff)
                else:
                    raise ValidationError(_(
                        'Không thể bắt đầu sản xuất!\n'
                        'Các phân loại đã chọn của loài gỗ "%s" trong Hồ sơ "%s" không đủ tồn kho khả dụng.\n'
                        'Kế hoạch cần dùng: %.2f m³ — Thiếu: %.2f m³'
                    ) % (line.species_id.name, line.dossier_id.name, line.volume_planned, vol_remaining))
                    
        # Kiểm tra tồn kho khả dụng cho Ván bóc
        for p_line in self.peeling_line_ids:
            if not p_line.peeling_dossier_id or not p_line.peeling_type_id:
                continue
            vol_needed = p_line.volume_planned
            lines_to_use = p_line.peeling_dossier_line_ids or p_line.peeling_dossier_id.line_ids.filtered(lambda dl: dl.peeling_type_id == p_line.peeling_type_id)
            if not lines_to_use:
                raise ValidationError(_('Hồ sơ "%s" không có loại ván bóc "%s"!') % (p_line.peeling_dossier_id.name, p_line.peeling_type_id.name))
            
            avail_qty = sum(lines_to_use.mapped('qty_available'))
            if avail_qty < vol_needed - 0.05:
                raise ValidationError(_('Không đủ tồn kho Ván Bóc!\nLoại: %s\nHồ sơ: %s\nKế hoạch cần dùng: %.2f m³ — Hiện có: %.2f m³') % (p_line.peeling_type_id.name, p_line.peeling_dossier_id.name, vol_needed, avail_qty))

        self.state = 'in_progress'

    def action_done(self):
        """Hoàn thành lệnh sản xuất và trừ lùi nguyên liệu."""
        self.ensure_one()
        if not self.line_ids and not self.peeling_line_ids:
            raise UserError(_('Vui lòng nhập chi tiết tiêu hao nguyên vật liệu trước khi hoàn thành.'))
        self._action_deduct_materials()
        self._action_deduct_peeling_materials()
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
                
            # Hoàn trả lại số lượng ván bóc đã dùng
            for p_line in self.peeling_line_ids:
                if p_line.peeling_dossier_id and p_line.volume_actual:
                    lines_to_use = p_line.peeling_dossier_line_ids or p_line.peeling_dossier_id.line_ids.filtered(lambda dl: dl.peeling_type_id == p_line.peeling_type_id)
                    vol_to_refund = p_line.volume_actual
                    for dossier_line in reversed(lines_to_use):
                        if vol_to_refund <= 0:
                            break
                        used = dossier_line.qty_used
                        if used >= vol_to_refund:
                            dossier_line.qty_used -= vol_to_refund
                            vol_to_refund = 0.0
                        else:
                            dossier_line.qty_used = 0.0
                            vol_to_refund -= used
                    _logger.info(f"Đã hoàn trả {p_line.volume_actual} m3 ván bóc cho hồ sơ {p_line.peeling_dossier_id.name}")

            self.date_done = False
            self.state = 'in_progress'
            _logger.info(f"Lệnh sản xuất {self.name} đã được hoàn trả nguyên vật liệu và chuyển về Đang sản xuất.")
        else:
            raise UserError(_('Không hỗ trợ quay lại trạng thái trước từ trạng thái hiện tại.'))

    def _action_deduct_materials(self, force=False):
        """Trừ khối lượng gỗ thực tế từ các hồ sơ gỗ liên quan theo từng dòng chi tiết phân loại cụ thể."""
        line_avail_cache = {}
        
        for line in self.line_ids:
            if not line.dossier_id or not line.species_id:
                continue
            
            vol_needed = line.volume_actual
            dossier = line.dossier_id
            species = line.species_id
            
            # Lấy các dòng chi tiết được chọn hoặc tất cả dòng cùng loài gỗ
            lines_to_use = line.x_dossier_line_ids or dossier.line_ids.filtered(lambda dl: dl.species_id == species)
            if not lines_to_use:
                raise ValidationError(_(
                    'Hồ sơ gỗ "%s" không có loài gỗ "%s"!'
                ) % (dossier.name, species.name))
                
            # Sắp xếp các dòng: chiều dài giảm dần, sau đó là ID tăng dần
            def sort_key(dl):
                origin_id = dl._origin.id if dl._origin else False
                val_id = origin_id if isinstance(origin_id, int) else (dl.id if isinstance(dl.id, int) else id(dl.id))
                return (dl.height, -val_id)
            sorted_lines = lines_to_use.sorted(key=sort_key, reverse=True)
            
            vol_remaining = vol_needed
            allocations = []
            for dossier_line in sorted_lines:
                if vol_remaining <= 0:
                    break
                if dossier_line.id not in line_avail_cache:
                    line_avail_cache[dossier_line.id] = dossier_line.x_qty_available
                
                avail = line_avail_cache[dossier_line.id]
                if avail <= 0:
                    continue
                    
                if avail >= vol_remaining:
                    allocated = vol_remaining
                    line_avail_cache[dossier_line.id] -= vol_remaining
                    vol_remaining = 0.0
                else:
                    allocated = avail
                    line_avail_cache[dossier_line.id] = 0.0
                    vol_remaining -= avail
                
                allocations.append((dossier_line, allocated))
            
            if not force and vol_remaining > 0:
                diff = vol_remaining
                if diff <= 0.05 and allocations:
                    # Chấp nhận sai số làm tròn nhỏ, cộng vào phần phân bổ cuối cùng
                    last_line, last_qty = allocations[-1]
                    allocations[-1] = (last_line, last_qty + diff)
                    vol_remaining = 0.0
                else:
                    raise ValidationError(_(
                        'Các phân loại đã chọn của loài gỗ "%s" trong Hồ sơ "%s" không đủ tồn kho khả dụng!\n'
                        'KL yêu cầu: %.2f m³ — Thiếu: %.2f m³'
                    ) % (species.name, dossier.name, vol_needed, vol_remaining))
            
            # Tạo các bản ghi vào sổ cái (Ledger) tương ứng cho từng dòng chi tiết được trừ
            for dossier_line, allocated_qty in allocations:
                if allocated_qty > 0.0001:
                    self.env['dl.dossier.ledger'].create({
                        'dossier_id': dossier.id,
                        'species_id': species.id,
                        'dossier_line_id': dossier_line.id,
                        'production_id': self.id,
                        'actual_qty': -allocated_qty,  # Số âm vì là xuất nguyên liệu
                        'state': 'done',
                        'date': fields.Datetime.now(),
                    })

    def _action_deduct_peeling_materials(self, force=False):
        """Trừ khối lượng ván bóc thực tế từ các hồ sơ ván bóc."""
        for p_line in self.peeling_line_ids:
            if not p_line.peeling_dossier_id or not p_line.peeling_type_id:
                continue
            
            vol_needed = p_line.volume_actual
            lines_to_use = p_line.peeling_dossier_line_ids or p_line.peeling_dossier_id.line_ids.filtered(lambda dl: dl.peeling_type_id == p_line.peeling_type_id)
            
            vol_remaining = vol_needed
            for dossier_line in lines_to_use:
                if vol_remaining <= 0:
                    break
                avail = dossier_line.qty_available
                if avail <= 0:
                    continue
                
                if avail >= vol_remaining:
                    dossier_line.qty_used += vol_remaining
                    vol_remaining = 0.0
                else:
                    dossier_line.qty_used += avail
                    vol_remaining -= avail
            
            if not force and vol_remaining > 0.05:
                raise ValidationError(_(
                    'Không đủ tồn kho Ván Bóc để trừ lùi!\n'
                    'Loại: %s\nHồ sơ: %s\nThiếu: %.2f m³'
                ) % (p_line.peeling_type_id.name, p_line.peeling_dossier_id.name, vol_remaining))

    def write(self, vals):
        for rec in self:
            if rec.state in ('done', 'cancelled'):
                allowed_fields = {'note', 'date_done', 'state', 'sale_order_id', 'partner_id', 'x_select_production_id'}
                for key, val in vals.items():
                    if key not in allowed_fields:
                        # Lấy giá trị hiện tại từ database
                        current_val = rec[key]
                        
                        # So sánh chi tiết từng kiểu dữ liệu
                        # 1. Đối với Many2one
                        if isinstance(current_val, models.BaseModel):
                            current_val_id = current_val.id if current_val else False
                            new_val_id = val
                            if isinstance(val, (list, tuple)):
                                new_val_id = val[0] if val else False
                            elif isinstance(val, models.BaseModel):
                                new_val_id = val.id if val else False
                            
                            if current_val_id != new_val_id:
                                raise UserError(_('Không thể chỉnh sửa các thông tin nghiệp vụ của Lệnh sản xuất đã Hoàn thành hoặc Hủy (Trường thay đổi: %s).') % key)
                        
                        # 2. Đối với One2many / Many2many
                        elif rec._fields[key].type in ('one2many', 'many2many'):
                            if val:
                                raise UserError(_('Không thể chỉnh sửa các thông tin nghiệp vụ của Lệnh sản xuất đã Hoàn thành hoặc Hủy (Trường thay đổi: %s).') % key)
                        
                        # 3. Đối với các kiểu dữ liệu thường (Char, Float, Selection...)
                        else:
                            if isinstance(current_val, float) and isinstance(val, (int, float)):
                                if abs(current_val - float(val)) > 1e-5:
                                    raise UserError(_('Không thể chỉnh sửa các thông tin nghiệp vụ của Lệnh sản xuất đã Hoàn thành hoặc Hủy (Trường thay đổi: %s, Cũ: %s, Mới: %s).') % (key, current_val, val))
                            else:
                                if current_val != val:
                                    raise UserError(_('Không thể chỉnh sửa các thông tin nghiệp vụ của Lệnh sản xuất đã Hoàn thành hoặc Hủy (Trường thay đổi: %s, Cũ: %s, Mới: %s).') % (key, current_val, val))
        return super(DlWoodProductionOrder, self).write(vals)

    def unlink(self):
        for rec in self:
            if rec.state in ('done', 'cancelled'):
                raise UserError(_('Không thể xóa Lệnh sản xuất đã Hoàn thành hoặc Hủy.'))
        
        records_to_unlink = self.env['dl.wood.production.order']
        for rec in self:
            if rec.x_select_production_id and rec.sale_order_id:
                rec.write({'sale_order_id': False})
            else:
                records_to_unlink += rec
        return super(DlWoodProductionOrder, records_to_unlink).unlink()

    def action_unlink_from_sale_order(self):
        for rec in self:
            rec.write({'sale_order_id': False})
        return True


class DlWoodProductionLine(models.Model):
    """Chi tiết tiêu hao nguyên vật liệu của một lệnh sản xuất."""
    _name = 'dl.wood.production.line'
    _description = 'Chi tiết NVL tiêu hao lệnh sản xuất'

    production_order_id = fields.Many2one(
        'dl.wood.production.order', string='Lệnh sản xuất',
        ondelete='cascade', required=True, index=True
    )
    x_sale_order_id = fields.Many2one(
        'dl.wood.sale.order',
        related='production_order_id.sale_order_id',
        string='Đơn đặt hàng',
        store=True,
        index=True
    )
    x_partner_id = fields.Many2one(
        'res.partner',
        related='x_sale_order_id.partner_id',
        string='Khách hàng (Đầy đủ)',
        store=True,
        readonly=True,
        index=True
    )
    x_partner_short_name = fields.Char(
        string='Khách hàng',
        related='x_partner_id.x_short_name',
        store=True,
        readonly=True,
        index=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Công ty',
        related='production_order_id.company_id',
        store=True,
        index=True
    )
    x_qty_planned = fields.Float(
        related='production_order_id.qty_planned',
        string='SL kế hoạch cha',
        readonly=True
    )
    x_qty_done = fields.Float(
        related='production_order_id.qty_done',
        string='SL thực tế cha',
        readonly=True
    )
    x_product_id = fields.Many2one(
        'product.product',
        related='production_order_id.product_id',
        string='Sản phẩm cha',
        readonly=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Tiền tệ',
        readonly=True
    )
    species_id = fields.Many2one('dl.wood.species', string='Loại gỗ', required=True)
    dossier_id = fields.Many2one(
        'dl.wood.dossier', string='Hồ sơ gỗ nguồn',
        domain="[('company_id', '=', company_id), ('state', '=', 'using')]",
        help='Hồ sơ gỗ mà nguyên liệu được lấy từ đó để sản xuất.'
    )
    x_available_species_ids = fields.Many2many(
        'dl.wood.species',
        compute='_compute_x_available_species_ids',
        string='Loài gỗ khả dụng'
    )
    x_dossier_line_ids = fields.Many2many(
        'dl.wood.dossier.line',
        'dl_wood_production_line_dossier_line_rel',
        'prod_line_id', 'dossier_line_id',
        string='Phân loại gỗ chi tiết',
        domain="[('dossier_id', '=', dossier_id), ('species_id', '=', species_id)]"
    )
    x_allocation_info = fields.Text(
        string='Chi tiết phân bổ tiêu hao',
        compute='_compute_x_allocation_info'
    )
    x_ratio = fields.Float(string='Định mức %', digits=(16, 2), default=0.0)
    x_co_yield = fields.Float(string='Khai CO', digits=(16, 2), default=1.3, help='Hệ số hao hụt nguyên vật liệu/thành phẩm của bộ hồ sơ này.')
    volume_planned = fields.Float(string='KL kế hoạch (m³)', digits=(16, 2))
    volume_actual = fields.Float(string='KL thực tế (m³)', digits=(16, 2))
    note = fields.Char(string='Ghi chú')
    x_price_unit = fields.Float(
        string='Đơn giá gỗ (VND/m³)',
        compute='_compute_x_price_unit',
        store=True,
        digits=(16, 2)
    )
    x_subtotal_cost = fields.Float(
        string='Thành tiền gỗ (VND)',
        compute='_compute_x_subtotal_cost',
        store=True,
        digits=(16, 2)
    )
    x_qty_available = fields.Float(
        string='Khối lượng khả dụng (m³)',
        compute='_compute_x_qty_available',
        digits=(16, 2)
    )

    @api.depends('dossier_id', 'species_id')
    def _compute_x_price_unit(self):
        for line in self:
            price = 0.0
            if line.dossier_id and line.species_id:
                dossier_line = line.dossier_id.line_ids.filtered(lambda dl: dl.species_id == line.species_id)
                if dossier_line:
                    price = dossier_line[0].price_unit
            line.x_price_unit = price

    @api.depends('volume_actual', 'volume_planned', 'x_price_unit', 'production_order_id.state')
    def _compute_x_subtotal_cost(self):
        for line in self:
            order = line.production_order_id
            # Nếu là Dự thảo (draft), dùng volume_planned, ngược lại dùng volume_actual
            vol = line.volume_planned if order and order.state == 'draft' else line.volume_actual
            line.x_subtotal_cost = round(vol * line.x_price_unit, 2)

    @api.depends('dossier_id', 'species_id', 'x_dossier_line_ids', 'x_dossier_line_ids.x_qty_available')
    def _compute_x_qty_available(self):
        for line in self:
            qty = 0.0
            if line.dossier_id and line.species_id:
                if line.x_dossier_line_ids:
                    qty = sum(line.x_dossier_line_ids.mapped('x_qty_available'))
                else:
                    same_species_lines = line.dossier_id.line_ids.filtered(lambda dl: dl.species_id == line.species_id)
                    qty = sum(same_species_lines.mapped('x_qty_available'))
            line.x_qty_available = qty

    @api.depends('dossier_id')
    def _compute_x_available_species_ids(self):
        for line in self:
            if line.dossier_id:
                species_ids = line.dossier_id.line_ids.mapped('species_id').ids
                line.x_available_species_ids = [(6, 0, species_ids)]
            else:
                line.x_available_species_ids = [(6, 0, [])]

    def _get_allocated_volumes(self):
        self.ensure_one()
        res = {}
        if self.x_dossier_line_ids:
            lines = self.x_dossier_line_ids
        elif self.dossier_id and self.species_id:
            lines = self.dossier_id.line_ids.filtered(lambda l: l.species_id == self.species_id)
        else:
            lines = self.env['dl.wood.dossier.line']

        if not lines:
            return res

        # Nếu lệnh sản xuất đã hoàn thành, đọc trực tiếp số đã trừ từ Sổ cái
        if self.production_order_id.state == 'done':
            ledgers = self.env['dl.dossier.ledger'].search([
                ('production_id', '=', self.production_order_id.id),
                ('dossier_line_id', 'in', lines.ids)
            ])
            for ledger in ledgers:
                res[ledger.dossier_line_id] = abs(ledger.actual_qty)
            for l in lines:
                if l not in res:
                    res[l] = 0.0
            return res

        vol_to_allocate = self.volume_planned if self.production_order_id.state == 'draft' else self.volume_actual
        # Sắp xếp các dòng: chiều dài giảm dần, sau đó là ID tăng dần
        def sort_key(dl):
            origin_id = dl._origin.id if dl._origin else False
            val_id = origin_id if isinstance(origin_id, int) else (dl.id if isinstance(dl.id, int) else id(dl.id))
            return (dl.height, -val_id)
        sorted_lines = lines.sorted(key=sort_key, reverse=True)

        remaining_vol = vol_to_allocate
        for l in sorted_lines:
            avail = l.x_qty_available
            if remaining_vol <= 0:
                res[l] = 0.0
            elif avail >= remaining_vol:
                res[l] = remaining_vol
                remaining_vol = 0.0
            else:
                res[l] = avail
                remaining_vol -= avail
        return res

    @api.depends('volume_planned', 'volume_actual', 'x_dossier_line_ids', 'dossier_id', 'species_id', 'production_order_id.state')
    def _compute_x_allocation_info(self):
        for line in self:
            if not line.dossier_id or not line.species_id:
                line.x_allocation_info = ""
                continue

            allocated = line._get_allocated_volumes()
            if not allocated:
                line.x_allocation_info = "Không có phân loại nào khả dụng."
                continue

            lines_info = []
            def sort_key(item):
                dl = item[0]
                origin_id = dl._origin.id if dl._origin else False
                val_id = origin_id if isinstance(origin_id, int) else (dl.id if isinstance(dl.id, int) else id(dl.id))
                return (dl.height, -val_id)
            sorted_allocated = sorted(allocated.items(), key=sort_key, reverse=True)
            for dossier_line, vol in sorted_allocated:
                grade_name = dossier_line.grade_id.name or "Mặc định"
                dim_str = f"L dài: {dossier_line.height}m" if dossier_line.height else "L dài: N/A"
                if dossier_line.diameter_min or dossier_line.diameter_max:
                    dim_str += f", ĐK: {dossier_line.diameter_min}-{dossier_line.diameter_max}cm"

                lines_info.append(
                    f"• {grade_name} ({dim_str}): Sử dụng {vol:.2f} m³ / Tồn {dossier_line.x_qty_available:.2f} m³"
                )
            line.x_allocation_info = "\n".join(lines_info)

    def _get_vol_per_unit(self):
        self.ensure_one()
        product = self.x_product_id or self.production_order_id.product_id
        if not product:
            return 1.0

        x_unit_val = getattr(product, 'x_unit', '')
        if x_unit_val == 'm3':
            return 1.0

        if x_unit_val == 'sheet':
            vol_per_unit = product.x_volume_m3
            if not vol_per_unit:
                p = product
                if p.x_length and p.x_width and p.x_thickness:
                    area = (p.x_length * p.x_width) / 1_000_000.0
                    vol_per_unit = (area * p.x_thickness) / 1_000.0
            return vol_per_unit or 1.0

        uom_name = product.uom_id.name or ''
        if any(x in uom_name.lower() for x in ['m³', 'm3', 'mét khối', 'met khoi']):
            return 1.0

        vol_per_unit = product.x_volume_m3
        if not vol_per_unit:
            p = product
            if p.x_length and p.x_width and p.x_thickness:
                area = (p.x_length * p.x_width) / 1_000_000.0
                vol_per_unit = (area * p.x_thickness) / 1_000.0
        return vol_per_unit or 1.0

    def _update_ratio_and_volumes_from_lines(self):
        for line in self:
            if not line.dossier_id or not line.species_id:
                line.x_qty_available = 0.0
                line.x_ratio = 0.0
                line.volume_planned = 0.0
                line.volume_actual = 0.0
                continue

            # Tính toán tồn khả dụng real-time trực tiếp từ các dòng chi tiết được chọn
            if line.x_dossier_line_ids:
                avail_qty = sum(line.x_dossier_line_ids.mapped('x_qty_available'))
            else:
                same_species_lines = line.dossier_id.line_ids.filtered(lambda l: l.species_id == line.species_id)
                avail_qty = sum(same_species_lines.mapped('x_qty_available'))

            line.x_qty_available = avail_qty

            order = line.production_order_id
            if order:
                line.x_co_yield = order.x_co_yield
                vol_per_unit = line._get_vol_per_unit()

                # Lọc bỏ dòng hiện tại ra khỏi danh sách các dòng tiêu hao khác của Lệnh sản xuất
                def is_same_line(l1, l2):
                    if l1 == l2:
                        return True
                    if l1.id == l2.id:
                        return True
                    o1 = l1._origin if getattr(l1, '_origin', None) else l1
                    o2 = l2._origin if getattr(l2, '_origin', None) else l2
                    if o1 and o2 and o1.id == o2.id:
                        return True
                    return False

                other_lines = order.line_ids.filtered(lambda l: not is_same_line(l, line))

                qty_planned = line.x_qty_planned or order.qty_planned
                qty_done = line.x_qty_done or order.qty_done

                if qty_planned > 0:
                    total_volume_needed = (qty_planned * vol_per_unit) * line.x_co_yield
                    if total_volume_needed > 0:
                        other_lines_ratio_sum = sum(other_lines.mapped('x_ratio'))
                        peeling_lines_ratio_sum = sum(order.peeling_line_ids.mapped('x_ratio'))
                        remaining_ratio_needed = max(0.0, 100.0 - other_lines_ratio_sum - peeling_lines_ratio_sum)

                        raw_volume_needed = total_volume_needed * (remaining_ratio_needed / 100.0)
                        dossier_qty_avail = max(0.0, avail_qty)

                        if dossier_qty_avail >= raw_volume_needed:
                            line.x_ratio = round(remaining_ratio_needed, 2)
                        else:
                            allocated_ratio = (dossier_qty_avail / total_volume_needed) * 100.0
                            line.x_ratio = round(allocated_ratio, 2)

                        # Tính toán KL planned/actual của dòng
                        vol_plan = round(((qty_planned * vol_per_unit) * line.x_co_yield) * (line.x_ratio / 100.0), 2)
                        vol_act = round(((qty_done * vol_per_unit) * line.x_co_yield) * (line.x_ratio / 100.0), 2)

                        vol_plan = min(vol_plan, dossier_qty_avail)
                        vol_act = min(vol_act, dossier_qty_avail)
                        line.volume_planned = vol_plan
                        line.volume_actual = vol_act

    @api.onchange('dossier_id', 'species_id')
    def _onchange_dossier_and_species(self):
        if self.dossier_id:
            species_in_dossier = self.dossier_id.line_ids.mapped('species_id')
            if not self.species_id and len(species_in_dossier) == 1:
                self.species_id = species_in_dossier[0]

            if self.species_id:
                same_species_lines = self.dossier_id.line_ids.filtered(lambda l: l.species_id == self.species_id)
                self.x_dossier_line_ids = [(6, 0, same_species_lines.ids)]
            else:
                self.x_dossier_line_ids = [(6, 0, [])]

            self._update_ratio_and_volumes_from_lines()
        else:
            self.species_id = False
            self.x_dossier_line_ids = [(6, 0, [])]
            self.x_qty_available = 0.0
            self.x_ratio = 0.0
            self.volume_planned = 0.0
            self.volume_actual = 0.0

    @api.onchange('x_dossier_line_ids')
    def _onchange_x_dossier_line_ids(self):
        if self.x_dossier_line_ids and (self.dossier_id or self.species_id):
            valid_lines = self.x_dossier_line_ids.filtered(
                lambda l: (not self.dossier_id or l.dossier_id == self.dossier_id) and 
                          (not self.species_id or l.species_id == self.species_id)
            )
            if len(valid_lines) != len(self.x_dossier_line_ids):
                self.x_dossier_line_ids = [(6, 0, valid_lines.ids)]
        
        self._update_ratio_and_volumes_from_lines()

    @api.onchange('x_ratio', 'x_co_yield')
    def _onchange_ratio_and_co(self):
        for line in self:
            if line.x_ratio:
                order = line.production_order_id
                vol_per_unit = line._get_vol_per_unit()
                qty_planned = line.x_qty_planned or order.qty_planned
                qty_done = line.x_qty_done or order.qty_done
                vol_plan = round(((qty_planned * vol_per_unit) * line.x_co_yield) * (line.x_ratio / 100.0), 2)
                vol_act = round(((qty_done * vol_per_unit) * line.x_co_yield) * (line.x_ratio / 100.0), 2)
                if line.dossier_id:
                    if line.x_dossier_line_ids:
                        avail_qty = sum(line.x_dossier_line_ids.mapped('x_qty_available'))
                    else:
                        same_species_lines = line.dossier_id.line_ids.filtered(lambda l: l.species_id == line.species_id)
                        avail_qty = sum(same_species_lines.mapped('x_qty_available'))
                    vol_plan = min(vol_plan, avail_qty)
                    vol_act = min(vol_act, avail_qty)
                line.volume_planned = vol_plan
                line.volume_actual = vol_act

    @api.onchange('volume_planned')
    def _onchange_volume_planned(self):
        if self.volume_planned:
            if self.dossier_id:
                if self.x_dossier_line_ids:
                    avail_qty = sum(self.x_dossier_line_ids.mapped('x_qty_available'))
                else:
                    same_species_lines = self.dossier_id.line_ids.filtered(lambda l: l.species_id == self.species_id)
                    avail_qty = sum(same_species_lines.mapped('x_qty_available'))
                self.volume_planned = min(self.volume_planned, avail_qty)
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

class DlWoodPeelingProductionLine(models.Model):
    """Chi tiết tiêu hao Ván Bóc của lệnh sản xuất."""
    _name = 'dl.wood.peeling.production.line'
    _description = 'Chi tiết tiêu hao Ván Bóc'

    production_order_id = fields.Many2one(
        'dl.wood.production.order', string='Lệnh sản xuất',
        ondelete='cascade', required=True, index=True
    )
    company_id = fields.Many2one(
        'res.company', string='Công ty',
        related='production_order_id.company_id', store=True
    )
    currency_id = fields.Many2one(
        'res.currency', string='Tiền tệ',
        related='company_id.currency_id', readonly=True
    )
    x_sale_order_id = fields.Many2one(
        'dl.wood.sale.order',
        related='production_order_id.sale_order_id',
        string='Đơn đặt hàng',
        store=True,
        index=True
    )
    x_partner_id = fields.Many2one(
        'res.partner',
        related='x_sale_order_id.partner_id',
        string='Khách hàng (Đầy đủ)',
        store=True,
        readonly=True,
        index=True
    )
    x_partner_short_name = fields.Char(
        string='Khách hàng',
        related='x_partner_id.x_short_name',
        store=True,
        readonly=True,
        index=True
    )
    x_qty_planned = fields.Float(
        related='production_order_id.qty_planned',
        string='SL kế hoạch cha',
        readonly=True
    )
    x_qty_done = fields.Float(
        related='production_order_id.qty_done',
        string='SL thực tế cha',
        readonly=True
    )
    x_product_id = fields.Many2one(
        'product.product',
        related='production_order_id.product_id',
        string='Sản phẩm cha',
        readonly=True
    )
    peeling_dossier_id = fields.Many2one(
        'dl.wood.peeling.dossier', string='Hồ sơ ván bóc',
        domain="[('company_id', '=', company_id), ('state', '=', 'using')]",
        required=True
    )
    x_available_peeling_type_ids = fields.Many2many(
        'dl.wood.peeling.type',
        compute='_compute_x_available_peeling_type_ids',
        string='Loại ván bóc khả dụng'
    )
    peeling_type_id = fields.Many2one(
        'dl.wood.peeling.type', string='Loại ván bóc',
        required=True, domain="[('id', 'in', x_available_peeling_type_ids)]"
    )
    peeling_dossier_line_ids = fields.Many2many(
        'dl.wood.peeling.dossier.line',
        'dl_peeling_prod_line_dossier_line_rel',
        'prod_line_id', 'dossier_line_id',
        string='Phân loại chi tiết',
        domain="[('dossier_id', '=', peeling_dossier_id), ('peeling_type_id', '=', peeling_type_id)]"
    )
    x_qty_available = fields.Float(
        string='Tồn KD (m³)', compute='_compute_x_qty_available'
    )
    x_ratio = fields.Float(string='Định mức %', digits=(16, 2), default=0.0)
    x_co_yield = fields.Float(string='Khai CO', digits=(16, 2), default=1.1)
    volume_planned = fields.Float(string='KL kế hoạch (m³)', digits=(16, 2))
    volume_actual = fields.Float(string='KL thực tế (m³)', digits=(16, 2))
    x_price_unit = fields.Float(string='Đơn giá', compute='_compute_x_price_unit')
    x_subtotal_cost = fields.Float(string='Thành tiền', compute='_compute_x_subtotal_cost')
    note = fields.Char(string='Ghi chú')

    @api.depends('peeling_dossier_id')
    def _compute_x_available_peeling_type_ids(self):
        for line in self:
            if line.peeling_dossier_id:
                type_ids = line.peeling_dossier_id.line_ids.mapped('peeling_type_id').ids
                line.x_available_peeling_type_ids = [(6, 0, type_ids)]
            else:
                line.x_available_peeling_type_ids = [(6, 0, [])]

    @api.depends('peeling_dossier_id', 'peeling_type_id', 'peeling_dossier_line_ids', 'peeling_dossier_line_ids.qty_available')
    def _compute_x_qty_available(self):
        for line in self:
            qty = 0.0
            if line.peeling_dossier_id and line.peeling_type_id:
                if line.peeling_dossier_line_ids:
                    qty = sum(line.peeling_dossier_line_ids.mapped('qty_available'))
                else:
                    lines = line.peeling_dossier_id.line_ids.filtered(lambda l: l.peeling_type_id == line.peeling_type_id)
                    qty = sum(lines.mapped('qty_available'))
            line.x_qty_available = qty

    @api.depends('peeling_dossier_id', 'peeling_type_id')
    def _compute_x_price_unit(self):
        for line in self:
            price = 0.0
            if line.peeling_dossier_id and line.peeling_type_id:
                dossier_line = line.peeling_dossier_id.line_ids.filtered(lambda l: l.peeling_type_id == line.peeling_type_id)
                if dossier_line:
                    price = dossier_line[0].price_unit
            line.x_price_unit = price

    @api.depends('volume_actual', 'volume_planned', 'x_price_unit', 'production_order_id.state')
    def _compute_x_subtotal_cost(self):
        for line in self:
            order = line.production_order_id
            vol = line.volume_planned if order and order.state == 'draft' else line.volume_actual
            line.x_subtotal_cost = round(vol * line.x_price_unit, 2)

    def _get_vol_per_unit(self):
        self.ensure_one()
        product = self.production_order_id.product_id
        if not product: return 1.0
        x_unit_val = getattr(product, 'x_unit', '')
        if x_unit_val == 'm3': return 1.0
        if x_unit_val == 'sheet':
            vol_per_unit = product.x_volume_m3
            if not vol_per_unit and product.x_length and product.x_width and product.x_thickness:
                area = (product.x_length * product.x_width) / 1_000_000.0
                vol_per_unit = (area * product.x_thickness) / 1_000.0
            return vol_per_unit or 1.0
        uom_name = product.uom_id.name or ''
        if any(x in uom_name.lower() for x in ['m³', 'm3', 'mét khối', 'met khoi']):
            return 1.0
        vol_per_unit = product.x_volume_m3
        if not vol_per_unit and product.x_length and product.x_width and product.x_thickness:
            area = (product.x_length * product.x_width) / 1_000_000.0
            vol_per_unit = (area * product.x_thickness) / 1_000.0
        return vol_per_unit or 1.0

    def _update_ratio_and_volumes(self):
        for line in self:
            if not line.peeling_dossier_id or not line.peeling_type_id:
                line.x_qty_available = 0.0
                line.x_ratio = 0.0
                line.volume_planned = 0.0
                line.volume_actual = 0.0
                continue
                
            order = line.production_order_id
            vol_per_unit = line._get_vol_per_unit()
            qty_planned = order.qty_planned
            qty_done = order.qty_done
            
            if qty_planned > 0:
                total_volume_needed = (qty_planned * vol_per_unit) * line.x_co_yield
                if total_volume_needed > 0:
                    other_lines = order.peeling_line_ids.filtered(lambda l: l.id != line.id and getattr(l, '_origin', l).id != getattr(line, '_origin', line).id)
                    other_ratio = sum(other_lines.mapped('x_ratio'))
                    wood_ratio = sum(order.line_ids.mapped('x_ratio'))
                    remaining_ratio = max(0.0, 100.0 - other_ratio - wood_ratio)
                    
                    if line.peeling_dossier_line_ids:
                        avail_qty = sum(line.peeling_dossier_line_ids.mapped('qty_available'))
                    else:
                        lines = line.peeling_dossier_id.line_ids.filtered(lambda l: l.peeling_type_id == line.peeling_type_id)
                        avail_qty = sum(lines.mapped('qty_available'))
                    
                    raw_volume_needed = total_volume_needed * (remaining_ratio / 100.0)
                    if avail_qty >= raw_volume_needed:
                        line.x_ratio = round(remaining_ratio, 2)
                    else:
                        allocated_ratio = (avail_qty / total_volume_needed) * 100.0
                        line.x_ratio = round(allocated_ratio, 2)
                        
                    vol_plan = round(((qty_planned * vol_per_unit) * line.x_co_yield) * (line.x_ratio / 100.0), 2)
                    vol_act = round(((qty_done * vol_per_unit) * line.x_co_yield) * (line.x_ratio / 100.0), 2)
                    
                    line.volume_planned = min(vol_plan, avail_qty)
                    line.volume_actual = min(vol_act, avail_qty)

    @api.onchange('peeling_dossier_id', 'peeling_type_id')
    def _onchange_dossier_and_type(self):
        if self.peeling_dossier_id:
            types_in_dossier = self.peeling_dossier_id.line_ids.mapped('peeling_type_id')
            if not self.peeling_type_id and len(types_in_dossier) == 1:
                self.peeling_type_id = types_in_dossier[0]

            if self.peeling_type_id:
                same_type_lines = self.peeling_dossier_id.line_ids.filtered(lambda l: l.peeling_type_id == self.peeling_type_id)
                self.peeling_dossier_line_ids = [(6, 0, same_type_lines.ids)]
            else:
                self.peeling_dossier_line_ids = [(6, 0, [])]

            self._update_ratio_and_volumes()
        else:
            self.peeling_type_id = False
            self.peeling_dossier_line_ids = [(6, 0, [])]
            self.x_qty_available = 0.0
            self.x_ratio = 0.0
            self.volume_planned = 0.0
            self.volume_actual = 0.0

    @api.onchange('peeling_dossier_line_ids')
    def _onchange_peeling_dossier_line_ids(self):
        if self.peeling_dossier_line_ids and (self.peeling_dossier_id or self.peeling_type_id):
            valid_lines = self.peeling_dossier_line_ids.filtered(
                lambda l: (not self.peeling_dossier_id or l.dossier_id == self.peeling_dossier_id) and 
                          (not self.peeling_type_id or l.peeling_type_id == self.peeling_type_id)
            )
            if len(valid_lines) != len(self.peeling_dossier_line_ids):
                self.peeling_dossier_line_ids = [(6, 0, valid_lines.ids)]
        self._update_ratio_and_volumes()

    @api.onchange('x_ratio', 'x_co_yield')
    def _onchange_ratio_and_co(self):
        if self.x_ratio:
            order = self.production_order_id
            vol_per_unit = self._get_vol_per_unit()
            qty_planned = order.qty_planned
            qty_done = order.qty_done
            vol_plan = round(((qty_planned * vol_per_unit) * self.x_co_yield) * (self.x_ratio / 100.0), 2)
            vol_act = round(((qty_done * vol_per_unit) * self.x_co_yield) * (self.x_ratio / 100.0), 2)
            if self.peeling_dossier_id:
                if self.peeling_dossier_line_ids:
                    avail_qty = sum(self.peeling_dossier_line_ids.mapped('qty_available'))
                else:
                    avail_qty = sum(self.peeling_dossier_id.line_ids.filtered(lambda l: l.peeling_type_id == self.peeling_type_id).mapped('qty_available'))
                vol_plan = min(vol_plan, avail_qty)
                vol_act = min(vol_act, avail_qty)
            self.volume_planned = vol_plan
            self.volume_actual = vol_act

    @api.onchange('volume_planned')
    def _onchange_volume_planned(self):
        if self.volume_planned:
            if self.peeling_dossier_id:
                if self.peeling_dossier_line_ids:
                    avail_qty = sum(self.peeling_dossier_line_ids.mapped('qty_available'))
                else:
                    avail_qty = sum(self.peeling_dossier_id.line_ids.filtered(lambda l: l.peeling_type_id == self.peeling_type_id).mapped('qty_available'))
                self.volume_planned = min(self.volume_planned, avail_qty)
            self.volume_actual = self.volume_planned

    def write(self, vals):
        for line in self:
            if line.production_order_id.state in ('done', 'cancelled'):
                raise UserError(_('Không thể chỉnh sửa tiêu hao nguyên vật liệu của Lệnh sản xuất đã Hoàn thành hoặc Hủy.'))
        return super(DlWoodPeelingProductionLine, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('production_order_id'):
                order = self.env['dl.wood.production.order'].browse(vals['production_order_id'])
                if order.state in ('done', 'cancelled'):
                    raise UserError(_('Không thể thêm tiêu hao nguyên vật liệu cho Lệnh sản xuất đã Hoàn thành hoặc Hủy.'))
        return super(DlWoodPeelingProductionLine, self).create(vals_list)

    def unlink(self):
        for line in self:
            if line.production_order_id.state in ('done', 'cancelled'):
                raise UserError(_('Không thể xóa tiêu hao nguyên vật liệu của Lệnh sản xuất đã Hoàn thành hoặc Hủy.'))
        return super(DlWoodPeelingProductionLine, self).unlink()
