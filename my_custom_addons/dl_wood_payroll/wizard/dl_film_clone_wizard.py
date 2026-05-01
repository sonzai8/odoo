# -*- coding: utf-8 -*-
"""Wizard cho phép clone bảng giá Ép Film từ tháng bất kỳ"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class FilmCloneWizard(models.TransientModel):
    _name = 'dl.film.clone.wizard'
    _description = 'Sao chép Bảng giá Ép Film từ tháng khác'

    target_pricelist_id = fields.Many2one(
        'dl.film.pricelist', string='Bảng giá Đích', required=True,
        help='Bảng giá hiện tại sẽ nhận dữ liệu được clone.'
    )
    source_pricelist_id = fields.Many2one(
        'dl.film.pricelist', string='Bảng giá Nguồn', required=True,
        domain=[('state', '=', 'confirmed')],
        help='Chọn bảng giá đã xác nhận để sao chép dữ liệu.'
    )

    def action_clone(self):
        """Thực hiện clone dữ liệu từ bảng nguồn sang bảng đích"""
        self.ensure_one()
        target = self.target_pricelist_id
        source = self.source_pricelist_id

        if target.state == 'confirmed':
            raise UserError(_("Bảng giá đích đã xác nhận, không thể ghi đè!"))

        if target.id == source.id:
            raise UserError(_("Bảng giá nguồn và đích không được trùng nhau!"))

        # Xóa dữ liệu cũ
        target.line_ids.unlink()

        # Clone từ nguồn
        vals_list = []
        for line in source.line_ids:
            vals_list.append({
                'pricelist_id': target.id,
                'product_tmpl_id': line.product_tmpl_id.id,
                'x_film_brand_id': line.x_film_brand_id.id,
                'x_surface_type': line.x_surface_type,
                'price_low': line.price_low,
                'price_high': line.price_high,
                'price_re_ep_low': line.price_re_ep_low,
                'price_re_ep_high': line.price_re_ep_high,
            })

        if vals_list:
            self.env['dl.film.pricelist.line'].create(vals_list)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sao chép thành công'),
                'message': _('Đã sao chép %d dòng từ bảng giá %s.') % (len(vals_list), source.name),
                'type': 'success',
                'sticky': False,
            }
        }
