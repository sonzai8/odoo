# -*- coding: utf-8 -*-
"""
dl.dossier.ledger - Sổ Cái Trừ Lùi Nội Bộ (Backend Ledger)

Mục đích: Bảng ghi log (Append-only) lưu vết mọi biến động của hồ sơ gỗ.
Bảng này chạy ngầm và KHÔNG cho phép người dùng sửa đổi trực tiếp.
Mọi giao dịch được tạo/cập nhật tự động thông qua business logic của sale.order.

Quy ước:
  - actual_qty lưu giá trị ÂM khi xuất (ví dụ: -20 m³).
  - actual_qty lưu giá trị DƯƠNG khi hoàn trả/hủy đơn.
"""
from odoo import models, fields


class DlDossierLedger(models.Model):
    _name = 'dl.dossier.ledger'
    _description = 'Sổ Cái Trừ Lùi Hồ Sơ Gỗ (Backend)'
    _order = 'date desc, id desc'

    # Không cho phép tạo/sửa/xóa thủ công từ giao diện
    _rec_name = 'dossier_id'

    # -------------------------------------------------------------------------
    # Relations
    # -------------------------------------------------------------------------
    dossier_id = fields.Many2one(
        'dl.wood.dossier',
        string='Hồ Sơ Gỗ',
        required=True,
        ondelete='cascade',
        index=True,
        help='Bộ hồ sơ kiểm lâm bị ảnh hưởng bởi giao dịch này.',
    )
    sale_id = fields.Many2one(
        'sale.order',
        string='Đơn Bán Hàng',
        ondelete='set null',
        index=True,
        help='Đơn bán hàng là nguồn gốc gây ra giao dịch này.',
    )
    product_id = fields.Many2one(
        'product.product',
        related='dossier_id.product_id',
        string='Loại Gỗ',
        store=True,
        readonly=True,
    )

    # -------------------------------------------------------------------------
    # Transaction Data
    # -------------------------------------------------------------------------
    actual_qty = fields.Float(
        string='Khối Lượng Biến Động (m³)',
        digits=(16, 4),
        help='Số lượng biến động. Lưu số ÂM khi xuất kho (ví dụ: -20 m³), số DƯƠNG khi hoàn trả.',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Đang Giữ Hàng (Reserved)'),
            ('done', 'Đã Trừ Thực Tế (Confirmed)'),
            ('cancel', 'Đã Hủy (Trả Lại)'),
        ],
        string='Trạng Thái',
        required=True,
        default='draft',
        index=True,
        help=(
            'draft: Hàng đang được giữ chờ xác nhận.\n'
            'done: Đã trừ thực tế vào tồn kho hồ sơ.\n'
            'cancel: Giao dịch đã hủy, hàng được trả lại.'
        ),
    )
    date = fields.Datetime(
        string='Thời Gian Phát Sinh',
        default=fields.Datetime.now,
        required=True,
        help='Thời điểm giao dịch được ghi nhận vào sổ cái.',
    )
