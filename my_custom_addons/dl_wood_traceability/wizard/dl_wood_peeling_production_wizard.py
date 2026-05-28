# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class DlWoodPeelingLineProductionWizard(models.TransientModel):
    _name = 'dl.wood.peeling.line.production.wizard'
    _description = 'Wizard Bóc Ván Từng Dòng'

    dossier_line_id = fields.Many2one('dl.wood.dossier.line', string='Dòng hồ sơ gỗ', required=True, ondelete='cascade', readonly=True)
    species_id = fields.Many2one('dl.wood.species', string='Loài gỗ', readonly=True)
    
    volume_wood = fields.Float('Khối lượng đem bóc (m³)', digits=(16, 2), required=True)
    yield_factor = fields.Float('Định mức tiêu hao', digits=(16, 2), default=1.4, required=True, help="Ví dụ: 1.4 m3 gỗ tròn bóc ra được 1 m3 ván bóc.")
    
    peeling_variant_id = fields.Many2one('dl.wood.peeling.variant', string='Kích thước ván bóc', required=True)
    
    volume_peeling = fields.Float('Khối lượng ván bóc (m³)', compute='_compute_volume_peeling', store=True, digits=(16, 2))

    @api.depends('volume_wood', 'yield_factor')
    def _compute_volume_peeling(self):
        for rec in self:
            if rec.yield_factor > 0:
                rec.volume_peeling = rec.volume_wood / rec.yield_factor
            else:
                rec.volume_peeling = 0.0

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id and self.env.context.get('active_model') == 'dl.wood.dossier.line':
            line = self.env['dl.wood.dossier.line'].browse(active_id)
            if line.wood_type == 'firewood':
                raise UserError(_("Củi không thể đem đi bóc ván!"))
            if line.x_qty_available <= 0:
                raise UserError(_("Dòng này đã được bóc hoặc sử dụng hết!"))
                
            res['dossier_line_id'] = line.id
            res['species_id'] = line.species_id.id
            res['volume_wood'] = line.x_qty_available
            res['yield_factor'] = 1.4
            
            # Auto select peeling variant
            ptypes = self.env['dl.wood.peeling.type'].search([('species_id', '=', line.species_id.id)])
            if ptypes:
                variants = self.env['dl.wood.peeling.variant'].search([('peeling_type_id', 'in', ptypes.ids)], limit=1)
                if variants:
                    res['peeling_variant_id'] = variants[0].id
        return res

    def action_confirm(self):
        self.ensure_one()
        line = self.dossier_line_id
        dossier = line.dossier_id
        
        _logger.info(f"--- BẮT ĐẦU BÓC VÁN: Hồ sơ gỗ {dossier.name} - Dòng {line.id} ---")
        
        if self.volume_wood <= 0:
            _logger.error("Lỗi: Khối lượng gỗ đem bóc <= 0")
            raise UserError(_('Khối lượng gỗ đem bóc phải lớn hơn 0!'))
        if self.volume_wood > line.x_qty_available + 0.05:
            _logger.error(f"Lỗi: Khối lượng đem bóc ({self.volume_wood}) vượt khả dụng ({line.x_qty_available})")
            raise UserError(_('Khối lượng đem bóc vượt quá số lượng gỗ khả dụng!'))
            
        # 1. Tìm hoặc Tạo Peeling Dossier
        _logger.info("Bước 1: Kiểm tra Hồ sơ ván bóc")
        if not dossier.peeling_dossier_id:
            peeling_dossier = self.env['dl.wood.peeling.dossier'].create({
                'x_dossier_name': f'Ván bóc từ {dossier.name}',
                'partner_id': dossier.partner_id.id,
                'date_received': fields.Date.context_today(self),
                'company_id': dossier.company_id.id,
                'x_forest_owner_id': dossier.partner_id.id,
                'x_exploitation_location_id': dossier.exploitation_location_id.id,
                'state': 'using',
                'wood_dossier_id': dossier.id,
            })
            dossier.peeling_dossier_id = peeling_dossier.id
            _logger.info(f"Đã tạo mới Hồ sơ ván bóc ID: {peeling_dossier.id}")
        else:
            peeling_dossier = dossier.peeling_dossier_id
            _logger.info(f"Đã tìm thấy Hồ sơ ván bóc cũ ID: {peeling_dossier.id}")
            
        # 2. Tìm Invoice hiện tại (nếu chưa có thì tạo)
        _logger.info("Bước 2: Xử lý Hóa đơn bóc ván")
        invoice_number = dossier.x_contract_number or dossier.x_bkls_number or dossier.name
        peeling_invoice = self.env['dl.wood.peeling.invoice'].search([
            ('dossier_id', '=', peeling_dossier.id)
        ], limit=1)
        
        if not peeling_invoice:
            peeling_invoice = self.env['dl.wood.peeling.invoice'].with_context(skip_wood_dossier_check=True).create({
                'invoice_number': invoice_number,
                'invoice_date': fields.Date.context_today(self),
                'dossier_id': peeling_dossier.id,
            })
            _logger.info(f"Đã tạo mới Hóa đơn bóc ván ID: {peeling_invoice.id}")
        else:
            _logger.info(f"Sử dụng Hóa đơn bóc ván hiện tại ID: {peeling_invoice.id}")
            
        # 3. Trừ Gỗ bằng cách ghi Sổ cái & Tạo dòng Invoice
        _logger.info("Bước 3: Trừ lùi gỗ vào sổ cái và tạo dòng chi tiết bóc ván")
        self.env['dl.dossier.ledger'].create({
            'dossier_id': dossier.id,
            'species_id': line.species_id.id,
            'dossier_line_id': line.id,
            'peeling_dossier_id': peeling_dossier.id,
            'actual_qty': -self.volume_wood,
            'state': 'done',
        })
        
        bkls_number = dossier.x_bkls_number or invoice_number
        bkls_date = dossier.x_bkls_date or fields.Date.context_today(self)
        
        peeling_bkls = self.env['dl.wood.peeling.bkls'].search([
            ('invoice_id', '=', peeling_invoice.id),
            ('bkls_number', '=', bkls_number)
        ], limit=1)
        
        if not peeling_bkls:
            peeling_bkls = self.env['dl.wood.peeling.bkls'].create({
                'invoice_id': peeling_invoice.id,
                'bkls_number': bkls_number,
                'bkls_date': bkls_date,
            })
        
        self.env['dl.wood.peeling.bkls.line'].create({
            'bkls_id': peeling_bkls.id,
            'peeling_variant_id': self.peeling_variant_id.id,
            'qty_initial': self.volume_peeling,
            'qty_used': 0.0,
            'price_unit': 0.0,
        })
        _logger.info(f"Đã tạo thành công dòng chi tiết ván bóc cho biến thể: {self.peeling_variant_id.name}")
        _logger.info("--- HOÀN TẤT LUỒNG BÓC VÁN ---")
        
        # Reload current view or show a notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Thành công"),
                'message': _("Đã bóc ván thành công! Khối lượng gỗ đã được trừ."),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'}
            }
        }
