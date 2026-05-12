# -*- coding: utf-8 -*-
"""
dl.wood.dossier - Hồ Sơ Gỗ (Master Data)

Mục đích: Lưu trữ thông tin tĩnh của bộ hồ sơ kiểm lâm/chủ rừng.
Tồn kho không lưu trực tiếp mà được tính toán tự động từ bảng Ledger (dl.dossier.ledger)
để đảm bảo tính nhất quán và tránh deadlock khi nhiều đơn hàng cùng truy cập.
"""
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class DlWoodSpecies(models.Model):
    _name = 'dl.wood.species'
    _description = 'Loại Gỗ Thu Mua'
    
    name = fields.Char(string='Tên Thông Thường', required=True)
    name_en = fields.Char(string='Tên Tiếng Anh')
    name_sci = fields.Char(string='Tên Khoa Học')
    material_name = fields.Char(string='Tên Nguyên Liệu')
    code = fields.Char(string='Mã Loại Gỗ')
    note = fields.Text(string='Ghi chú')

    grade_ids = fields.One2many(
        'dl.wood.species.grade',
        'species_id',
        string='Phân loại chất lượng'
    )

    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Tên loại gỗ đã tồn tại!')
    ]

class DlWoodSpeciesGrade(models.Model):
    _name = 'dl.wood.species.grade'
    _description = 'Phân loại chất lượng gỗ'

    species_id = fields.Many2one('dl.wood.species', string='Loại gỗ', ondelete='cascade', required=True)
    name = fields.Char(string='Tên phân loại', required=True, help='Ví dụ: Loại 1, Loại 2...')
    
    # Quy cách đường kính
    diameter_min = fields.Float(string='Đường kính từ (cm)', digits=(16, 2))
    diameter_max = fields.Float(string='Đường kính đến (cm)', digits=(16, 2))
    
    # Quy cách chiều cao
    height_min = fields.Float(string='Chiều cao từ (m)', digits=(16, 2))
    height_max = fields.Float(string='Chiều cao đến (m)', digits=(16, 2))
    
    default_price = fields.Float(string='Giá mặc định', digits=(16, 0))
    note = fields.Text(string='Ghi chú')

class DlWoodDossier(models.Model):
    _name = 'dl.wood.dossier'
    _inherit = ['dl.wood.log.mixin']
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
        string='Sản phẩm đại diện',
        required=False,
        help='Sản phẩm chính đại diện cho hồ sơ này để theo dõi kho.',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Chủ Rừng / Nhà Cung Cấp',
        help='Cá nhân hoặc tổ chức cung cấp gỗ cho hồ sơ này.',
    )
    
    partner_address = fields.Char(
        string='Địa chỉ chủ rừng',
        compute='_compute_partner_address',
        help='Địa chỉ đăng ký chính thức của chủ rừng.'
    )

    @api.depends('partner_id', 'partner_id.street', 'partner_id.city', 'partner_id.state_id')
    def _compute_partner_address(self):
        for rec in self:
            if rec.partner_id:
                addr = []
                if rec.partner_id.street: addr.append(rec.partner_id.street)
                if rec.partner_id.city: addr.append(rec.partner_id.city)
                if rec.partner_id.state_id: addr.append(rec.partner_id.state_id.name)
                rec.partner_address = ", ".join(addr)
            else:
                rec.partner_address = False
    
    exploitation_location_id = fields.Many2one(
        'dl.wood.exploitation.location',
        string='Địa điểm khai thác',
        help='Chọn địa điểm khai thác cụ thể của chủ rừng này.'
    )
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Tự động lọc hoặc chọn địa điểm chính của đối tác"""
        if self.partner_id:
            # Gợi ý địa điểm chính nếu có
            main_loc = self.partner_id.exploitation_location_ids.filtered(lambda l: l.is_main)
            if main_loc:
                self.exploitation_location_id = main_loc[0]
            else:
                self.exploitation_location_id = False
        else:
            self.exploitation_location_id = False

    date_received = fields.Date(
        string='Ngày Nhận Hồ Sơ',
        help='Ngày nhận bộ hồ sơ kiểm lâm về kho.',
    )
    initial_qty = fields.Float(
        string='Khối Lượng Ban Đầu (m³)',
        digits=(16, 2),
        help='Tổng khối lượng gỗ được cấp phép ban đầu trong hồ sơ.',
    )
    x_woodpro_id = fields.Char(string='ID WoodPro', index=True)
    x_mining_address = fields.Char(string='Địa chỉ khai thác (Gốc)', help='Địa chỉ text lấy từ API WoodPro')
    
    x_mining_method = fields.Selection([
        ('white', 'Khai thác trắng toàn bộ'),
        ('group', 'Khai thác theo đám')
    ], string='Phương thức khai thác', default='white')
    
    x_start_date = fields.Date(string='Ngày bắt đầu khai thác')
    x_end_date = fields.Date(string='Ngày kết thúc khai thác')
    x_addendum_num = fields.Char(string='Số phụ lục')
    
    state = fields.Selection([
        ('draft', 'Dự Thảo'),
        ('exploiting', 'Đang Khai Thác'),
        ('in_use', 'Đang Sử Dụng'),
        ('summary', 'Tổng Kết'),
        ('confirmed', 'Xác Nhận')
    ], string='Trạng thái', default='draft')

    x_area = fields.Float(string='Diện tích (ha)', digits=(16, 2))
    production_count = fields.Integer(
        string='Số LSX',
        compute='_compute_production_count',
        store=True,
        help='Số lượng lệnh sản xuất đã tiêu hao hồ sơ gỗ này.'
    )

    def _compute_production_count(self):
        for rec in self:
            # Tìm các dòng nguyên liệu dùng hồ sơ này
            lines = self.env['dl.wood.production.line'].search([('dossier_id', '=', rec.id)])
            # Lấy danh sách ID LSX duy nhất
            order_ids = lines.mapped('production_order_id').ids
            rec.production_count = len(set(order_ids))

    line_ids = fields.One2many(
        'dl.wood.dossier.line',
        'dossier_id',
        string='Chi tiết gỗ khai thác'
    )

    attachment_ids = fields.One2many(
        'dl.wood.dossier.attachment',
        'dossier_id',
        string='Tệp đính kèm WoodPro'
    )

    @api.model
    def _cron_update_states(self):
        """Cập nhật trạng thái hồ sơ gỗ tự động dựa trên ngày khai thác"""
        today = fields.Date.context_today(self)
        
        # 1. Draft -> Exploiting: Nếu hôm nay >= Ngày bắt đầu
        draft_dossiers = self.search([
            ('state', '=', 'draft'),
            ('x_start_date', '<=', today)
        ])
        if draft_dossiers:
            draft_dossiers.write({'state': 'exploiting'})
            _logger.info(f"WOODPRO: Tự động chuyển {len(draft_dossiers)} hồ sơ sang Đang Khai Thác")

        # 2. Exploiting -> Summary: Nếu hôm nay > Ngày kết thúc
        exploiting_dossiers = self.search([
            ('state', '=', 'exploiting'),
            ('x_end_date', '<', today)
        ])
        if exploiting_dossiers:
            exploiting_dossiers.write({'state': 'summary'})
            _logger.info(f"WOODPRO: Tự động chuyển {len(exploiting_dossiers)} hồ sơ sang Tổng Kết")

    def action_confirm(self):
        """Nút bấm để xác nhận hồ sơ gỗ"""
        for record in self:
            if record.state == 'confirmed':
                continue
            record.write({'state': 'confirmed'})

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
        digits=(16, 2),
        help='Tồn kho sau khi đã xác nhận xuất. = initial_qty + sum(actual_qty) của các dòng state=done.',
    )
    qty_reserved = fields.Float(
        string='Đang Giữ Đơn (m³)',
        compute='_compute_stock_quantities',
        store=True,
        digits=(16, 2),
        help='Khối lượng đang bị giữ bởi các đơn hàng chờ xử lý (state=draft).',
    )
    qty_available = fields.Float(
        string='Khả Dụng Để Bán (m³)',
        compute='_compute_stock_quantities',
        store=True,
        digits=(16, 2),
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

class DlWoodDossierLine(models.Model):
    _name = 'dl.wood.dossier.line'
    _description = 'Chi tiết gỗ trong hồ sơ'

    dossier_id = fields.Many2one('dl.wood.dossier', string='Hồ sơ gỗ', ondelete='cascade', required=True)
    partner_id = fields.Many2one('res.partner', related='dossier_id.partner_id', string='Chủ rừng', store=True, index=True)
    species_id = fields.Many2one('dl.wood.species', string='Loại gỗ thu mua')
    
    name = fields.Char(string='Tên loại gỗ')
    name_en = fields.Char(string='Tên tiếng Anh')
    name_sci = fields.Char(string='Tên khoa học')
    
    quantity = fields.Float(string='Số lượng', digits=(16, 2))
    price_unit = fields.Float(string='Đơn giá', digits=(16, 0))
    diameter_min = fields.Float(string='ĐK từ (cm)', digits=(16, 2))
    diameter_max = fields.Float(string='ĐK đến (cm)', digits=(16, 2))
    height_min = fields.Float(string='Cao từ (m)', digits=(16, 2))
    height_max = fields.Float(string='Cao đến (m)', digits=(16, 2))
    avg_diameter = fields.Float(string='Đường kính TB (cm)', digits=(16, 2))
    avg_height = fields.Float(string='Chiều cao TB (m)', digits=(16, 2))
    volume = fields.Float(string='Khối lượng (m³)', digits=(16, 2))
    
    note = fields.Text(string='Ghi chú')
    x_woodpro_id = fields.Char(string='ID WoodPro Line')

    @api.onchange('species_id')
    def _onchange_species_id(self):
        """Tự động điền tên tiếng anh và tên khoa học từ loại gỗ"""
        if self.species_id:
            self.name = self.species_id.name
            self.name_en = self.species_id.name_en
            self.name_sci = self.species_id.name_sci

class DlWoodDossierAttachment(models.Model):
    _name = 'dl.wood.dossier.attachment'
    _description = 'Tệp đính kèm hồ sơ gỗ từ WoodPro'

    dossier_id = fields.Many2one('dl.wood.dossier', string='Hồ sơ gỗ', ondelete='cascade')
    name = fields.Char(string='Tên tệp', required=True)
    url = fields.Char(string='URL tải tệp')
    x_woodpro_id = fields.Char(string='ID WoodPro File')
    status = fields.Char(string='Trạng thái WoodPro')
    file_type = fields.Char(string='Loại file (WoodPro)')

    def action_download_file(self):
        """Mở controller để tải file từ WoodPro thông qua Odoo"""
        self.ensure_one()
        if not self.file_type:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi',
                    'message': 'Không xác định được loại file để tải.',
                    'type': 'danger',
                }
            }
        
        # Chuyển hướng đến controller proxy
        download_url = f"/dl_wood/download_attachment/{self.id}"
        return {
            'type': 'ir.actions.act_url',
            'url': download_url,
            'target': 'self',
        }
