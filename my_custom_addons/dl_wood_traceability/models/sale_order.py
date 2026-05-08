# -*- coding: utf-8 -*-
"""
sale.order (Mở rộng) - Tích hợp Truy Xuất Gỗ vào Đơn Bán Hàng

Phase 2 bổ sung:
  - action_suggest_dossiers(): Thuật toán FIFO tự động gợi ý hồ sơ gỗ.
  - action_confirm(): Override để chốt Ledger (draft → done).
  - action_cancel(): Override để hủy Ledger (draft → cancel).
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrderWoodTraceability(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'dl.wood.log.mixin']

    co_declaration_ids = fields.One2many(
        'dl.co.declaration', 'sale_id', string='Bảng Kê Khai CO',
    )

    # -------------------------------------------------------------------------
    # FIFO Suggestion
    # -------------------------------------------------------------------------
    def action_suggest_dossiers(self):
        """
        Thuật toán FIFO: Tự động gợi ý và gán hồ sơ gỗ cho các dòng khai báo
        chưa có dossier_id, dựa trên date_received tăng dần.
        Nếu một dossier không đủ → chia nhỏ thành nhiều dòng.
        """
        self.ensure_one()
        if self.state in ('sale', 'done', 'cancel'):
            raise UserError(_("Không thể gợi ý hồ sơ khi đơn hàng đã được xác nhận hoặc hủy."))

        pending_lines = self.co_declaration_ids.filtered(
            lambda d: not d.dossier_id and d.finished_qty > 0
        )
        if not pending_lines:
            raise UserError(_("Không có dòng khai báo nào cần gán hồ sơ. Vui lòng thêm dòng với Thành phẩm và Khối lượng trước."))

        for line in pending_lines:
            remaining_need = line.finished_qty * line.standard_ratio
            if remaining_need <= 0:
                continue

            # Tìm dossier FIFO: date_received tăng dần, qty_available > 0
            dossiers = self.env['dl.wood.dossier'].search(
                [('qty_available', '>', 0)],
                order='date_received asc, id asc'
            )
            if not dossiers:
                raise UserError(_("Không còn hồ sơ gỗ nào có hàng khả dụng!"))

            first = True
            for dossier in dossiers:
                if remaining_need <= 1e-9:
                    break

                take_qty = min(dossier.qty_available, remaining_need)

                if first:
                    # Cập nhật dòng hiện tại
                    line.write({
                        'dossier_id': dossier.id,
                        'finished_qty': take_qty / (line.standard_ratio or 1.1),
                    })
                    first = False
                else:
                    # Tạo dòng mới cho phần còn lại (split FIFO)
                    self.env['dl.co.declaration'].create({
                        'sale_id': self.id,
                        'finished_product_id': line.finished_product_id.id,
                        'finished_qty': take_qty / (line.standard_ratio or 1.1),
                        'standard_ratio': line.standard_ratio,
                        'co_index': line.co_index,
                        'dossier_id': dossier.id,
                    })

                remaining_need -= take_qty

            if remaining_need > 1e-9:
                raise UserError(_(
                    "Không đủ gỗ trong kho để đáp ứng dòng '%s'.\n"
                    "Còn thiếu: %.4f m³"
                ) % (line.finished_product_id.name or '?', remaining_need))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Gợi ý FIFO thành công'),
                'message': _('Đã tự động gán hồ sơ gỗ theo nguyên tắc FIFO (nhập trước – xuất trước).'),
                'type': 'success',
                'sticky': False,
            },
        }

    # -------------------------------------------------------------------------
    # Confirm: draft → done
    # -------------------------------------------------------------------------
    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            ledgers = order.co_declaration_ids.mapped('ledger_id').filtered(
                lambda l: l.state == 'draft'
            )
            ledgers.write({'state': 'done'})
        return res

    # -------------------------------------------------------------------------
    # Cancel: draft → cancel
    # -------------------------------------------------------------------------
    def action_cancel(self):
        for order in self:
            ledgers = order.co_declaration_ids.mapped('ledger_id').filtered(
                lambda l: l.state in ('draft', 'done')
            )
            ledgers.write({'state': 'cancel'})
        return super().action_cancel()
