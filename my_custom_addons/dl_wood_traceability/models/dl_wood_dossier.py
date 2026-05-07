# -*- coding: utf-8 -*-
"""
dl.wood.dossier - Hồ Sơ Gỗ (Master Data)

Mục đích: Lưu trữ thông tin tĩnh của bộ hồ sơ kiểm lâm/chủ rừng.
Tồn kho không lưu trực tiếp mà được tính toán tự động từ bảng Ledger (dl.dossier.ledger)
để đảm bảo tính nhất quán và tránh deadlock khi nhiều đơn hàng cùng truy cập.
"""
from odoo import models, fields, api


class DlWoodDossier(models.Model):
    _name = 'dl.wood.dossier'
    _description = 'Hồ Sơ Gỗ (Kiểm Lâm / Chủ Rừng)'
    _rec_name = 'name'

    # -------------------------------------------------------------------------
    # Master Data Fields
    # -------------------------------------------------------------------------
    name = fields.Char(
        string='Mã Hồ Sơ',
        required=True,
        copy=False,
        help='Mã số hồ sơ kiểm lâm. Có thể nhập tay hoặc sinh tự động.',
    )
    product_id = fields.Many2one(
        'product.product',
        string='Loại Gỗ Nguyên Liệu',
        required=True,
        help='Loại gỗ nguyên liệu được cấp phép trong hồ sơ này.',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Chủ Rừng / Nhà Cung Cấp',
        help='Cá nhân hoặc tổ chức cung cấp gỗ cho hồ sơ này.',
    )
    date_received = fields.Date(
        string='Ngày Nhận Hồ Sơ',
        help='Ngày nhận bộ hồ sơ kiểm lâm về kho.',
    )
    initial_qty = fields.Float(
        string='Khối Lượng Ban Đầu (m³)',
        digits=(16, 4),
        help='Tổng khối lượng gỗ được cấp phép ban đầu trong hồ sơ.',
    )

    # -------------------------------------------------------------------------
    # Ledger Relation (Append-only log)
    # -------------------------------------------------------------------------
    ledger_ids = fields.One2many(
        'dl.dossier.ledger',
        'dossier_id',
        string='Sổ Cái Biến Động',
    )

    # -------------------------------------------------------------------------
    # Computed Stock Fields
    # -------------------------------------------------------------------------
    remaining_qty = fields.Float(
        string='Tồn Kho Thực Tế (m³)',
        compute='_compute_stock_quantities',
        store=True,
        digits=(16, 4),
        help='Tồn kho sau khi đã xác nhận xuất. = initial_qty + sum(actual_qty) của các dòng state=done.',
    )
    qty_reserved = fields.Float(
        string='Đang Giữ Đơn (m³)',
        compute='_compute_stock_quantities',
        store=True,
        digits=(16, 4),
        help='Khối lượng đang bị giữ bởi các đơn hàng chờ xử lý (state=draft).',
    )
    qty_available = fields.Float(
        string='Khả Dụng Để Bán (m³)',
        compute='_compute_stock_quantities',
        store=True,
        digits=(16, 4),
        help='Khối lượng còn có thể phân bổ cho đơn hàng mới. = remaining_qty - qty_reserved.',
    )

    @api.depends(
        'initial_qty',
        'ledger_ids.actual_qty',
        'ledger_ids.state',
    )
    def _compute_stock_quantities(self):
        """
        Tính toán các chỉ số tồn kho từ bảng Ledger.
        actual_qty trong Ledger lưu số âm (xuất) nên tổng sẽ làm giảm tồn.
        """
        for dossier in self:
            done_lines = dossier.ledger_ids.filtered(lambda l: l.state == 'done')
            draft_lines = dossier.ledger_ids.filtered(lambda l: l.state == 'draft')

            # Tồn thực tế = ban đầu + tổng biến động đã xác nhận (âm = xuất)
            dossier.remaining_qty = dossier.initial_qty + sum(done_lines.mapped('actual_qty'))

            # Hàng đang bị giữ = giá trị tuyệt đối các dòng draft (âm)
            dossier.qty_reserved = abs(sum(draft_lines.mapped('actual_qty')))

            # Khả dụng = tồn thực - đang giữ
            dossier.qty_available = dossier.remaining_qty - dossier.qty_reserved
