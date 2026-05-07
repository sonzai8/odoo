# -*- coding: utf-8 -*-
"""
dl.co.declaration - Bảng Kê Khai CO Hải Quan (Frontend Declaration)

Bóc tách thiết kế:
  - actual_deduct_qty: Hệ số thực tế → trừ kho nội bộ (Backend Ledger).
  - co_declare_qty:    Hệ số CO      → in báo cáo khai báo nhà nước.

Phase 2 bổ sung:
  - Reservation Bridge: create/write/unlink tự động đồng bộ bản ghi Ledger.
  - Constraint: chặn trừ âm kho trước khi ghi.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class DlCoDeclaration(models.Model):
    _name = 'dl.co.declaration'
    _description = 'Bảng Kê Khai CO Hải Quan (Frontend)'
    _rec_name = 'dossier_id'

    # -------------------------------------------------------------------------
    # Relations
    # -------------------------------------------------------------------------
    sale_id = fields.Many2one(
        'sale.order', string='Đơn Hàng', required=True, ondelete='cascade', index=True,
    )
    dossier_id = fields.Many2one(
        'dl.wood.dossier', string='Hồ Sơ Gỗ',
        help='Chỉ chọn hồ sơ còn khả dụng (qty_available > 0).',
    )
    finished_product_id = fields.Many2one(
        'product.product', string='Thành Phẩm Bán Ra',
    )
    # Ledger entry được tạo tự động – không cho user sửa trực tiếp
    ledger_id = fields.Many2one(
        'dl.dossier.ledger', string='Ledger Entry',
        ondelete='set null', readonly=True, copy=False, index=True,
    )

    # -------------------------------------------------------------------------
    # Quantity & Ratio Fields
    # -------------------------------------------------------------------------
    finished_qty = fields.Float(string='KL Thành Phẩm (m³)', digits=(16, 4))
    standard_ratio = fields.Float(
        string='Định Mức Thực Tế', default=1.1, readonly=True, digits=(16, 4),
        help='Cấu hình sẵn, không cho phép sửa.',
    )
    actual_deduct_qty = fields.Float(
        string='KL Trừ Kho TT (m³)', compute='_compute_qty_fields', store=True, digits=(16, 4),
        help='= finished_qty × standard_ratio',
    )
    co_index = fields.Float(string='Hệ Số CO', default=1.3, digits=(16, 4))
    co_declare_qty = fields.Float(
        string='KL Khai Báo CO (m³)', compute='_compute_qty_fields', store=True, digits=(16, 4),
        help='= finished_qty × co_index',
    )

    # -------------------------------------------------------------------------
    # Compute
    # -------------------------------------------------------------------------
    @api.depends('finished_qty', 'standard_ratio', 'co_index')
    def _compute_qty_fields(self):
        for rec in self:
            rec.actual_deduct_qty = rec.finished_qty * rec.standard_ratio
            rec.co_declare_qty = rec.finished_qty * rec.co_index

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _calc_deduct(self, vals=None):
        """Tính actual_deduct_qty từ vals hoặc record hiện tại (an toàn trước recompute)."""
        fqty = vals.get('finished_qty', self.finished_qty) if vals else self.finished_qty
        ratio = vals.get('standard_ratio', self.standard_ratio) if vals else self.standard_ratio
        return fqty * ratio

    def _get_dossier(self, vals=None):
        """Lấy dossier từ vals (id) hoặc record hiện tại."""
        if vals and 'dossier_id' in vals:
            did = vals['dossier_id']
            return self.env['dl.wood.dossier'].browse(did) if did else self.env['dl.wood.dossier']
        return self.dossier_id

    def _validate_stock(self, new_deduct, new_dossier):
        """Chặn trừ âm kho. Cộng lại phần đang giữ của dòng này nếu cùng dossier."""
        if not new_dossier or new_deduct <= 0:
            return
        # Lượng hiện tại dòng này đang giữ ở dossier này (nếu có)
        own_reserve = 0.0
        if self.ledger_id and self.ledger_id.dossier_id.id == new_dossier.id:
            own_reserve = abs(self.ledger_id.actual_qty)
        effective_avail = new_dossier.qty_available + own_reserve
        if new_deduct > effective_avail + 1e-9:
            raise ValidationError(_(
                "Hồ sơ gỗ '%(dossier)s' không đủ khối lượng khả dụng!\n"
                "Cần: %(need).4f m³  |  Khả dụng: %(avail).4f m³"
            ) % {'dossier': new_dossier.name, 'need': new_deduct, 'avail': effective_avail})

    def _sync_ledger(self, deduct_qty, dossier):
        """Tạo / cập nhật / xóa ledger entry tương ứng với dòng khai báo này."""
        self.ensure_one()
        if dossier and deduct_qty > 0:
            if self.ledger_id:
                self.ledger_id.write({
                    'dossier_id': dossier.id,
                    'actual_qty': -deduct_qty,
                })
            else:
                ledger = self.env['dl.dossier.ledger'].create({
                    'dossier_id': dossier.id,
                    'sale_id': self.sale_id.id,
                    'actual_qty': -deduct_qty,
                    'state': 'draft',
                })
                # Bypass ORM write loop bằng SQL để tránh đệ quy
                self.env.cr.execute(
                    "UPDATE dl_co_declaration SET ledger_id = %s WHERE id = %s",
                    (ledger.id, self.id)
                )
                self.invalidate_recordset(['ledger_id'])
        else:
            # Không còn dossier hoặc qty = 0 → giải phóng reservation
            if self.ledger_id:
                self.ledger_id.unlink()
                self.env.cr.execute(
                    "UPDATE dl_co_declaration SET ledger_id = NULL WHERE id = %s", (self.id,)
                )
                self.invalidate_recordset(['ledger_id'])

    # -------------------------------------------------------------------------
    # Reservation Bridge – CRUD Overrides
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            deduct = rec._calc_deduct()
            dossier = rec.dossier_id
            rec._validate_stock(deduct, dossier)
            rec._sync_ledger(deduct, dossier)
        return records

    def write(self, vals):
        # Xác định trường có thể ảnh hưởng đến ledger
        ledger_fields = {'finished_qty', 'standard_ratio', 'dossier_id'}
        needs_sync = bool(vals.keys() & ledger_fields)

        if needs_sync:
            for rec in self:
                new_deduct = rec._calc_deduct(vals)
                new_dossier = rec._get_dossier(vals)
                rec._validate_stock(new_deduct, new_dossier)

        result = super().write(vals)

        if needs_sync:
            for rec in self:
                rec._sync_ledger(rec._calc_deduct(), rec.dossier_id)

        return result

    def unlink(self):
        # Giải phóng reservation trước khi xóa dòng
        ledgers = self.mapped('ledger_id').filtered(lambda l: l.state == 'draft')
        result = super().unlink()
        ledgers.unlink()
        return result
