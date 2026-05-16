# -*- coding: utf-8 -*-
"""
dl.wood.dossier - Hồ Sơ Gỗ (Master Data)
"""
from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError
import logging
import io
import base64
import os
import re
import zipfile

try:
    from docxtpl import DocxTemplate
except ImportError:
    DocxTemplate = None

_logger = logging.getLogger(__name__)


def date_to_vietnamese_text(d):
    """Chuyển đổi date object sang chuỗi: ngày 06 tháng 04 năm 2026"""
    if not d:
        return ""
    return f"ngày {d.day:02d} tháng {d.month:02d} năm {d.year}"


def no_accent_vietnamese(s):
    """Chuyển đổi tiếng Việt có dấu sang không dấu và chuẩn hóa cho tên file"""
    if not s: return ""
    s = s.lower()
    map_chars = {
        'a': 'áàảãạăắằẳẵặâấầẩẫậ',
        'd': 'đ',
        'e': 'éèẻẽẹêếềểễệ',
        'i': 'íìỉĩị',
        'o': 'óòỏõọôốồổỗộơớờởỡợ',
        'u': 'úùủũụưứừửữự',
        'y': 'ýỳỷỹỵ',
    }
    for dest, src in map_chars.items():
        for char in src:
            s = s.replace(char, dest)
    # Loại bỏ ký tự đặc biệt, thay khoảng trắng bằng gạch dưới
    import re
    s = re.sub(r'[^a-z0-9\s]', '', s)
    s = re.sub(r'\s+', '_', s.strip())
    return s.upper()


    return f"ngày {d.day:02d} tháng {d.month:02d} năm {d.year}"


class DlWoodPdfMixin(models.AbstractModel):
    _name = 'dl.wood.pdf.mixin'
    _description = 'Hỗ trợ chuyển đổi PDF'

    def _get_soffice_path(self):
        """Tìm đường dẫn thực thi của LibreOffice (soffice)"""
        import shutil
        import os
        possible_paths = [
            'soffice',
            '/Applications/LibreOffice.app/Contents/MacOS/soffice',
            '/usr/bin/soffice',
            '/usr/local/bin/soffice'
        ]
        for p in possible_paths:
            if shutil.which(p) or os.path.exists(p):
                return p
        return None

    def _convert_docx_to_pdf(self, docx_content):
        """Chuyển đổi DOCX sang PDF sử dụng LibreOffice"""
        import subprocess
        import tempfile
        import os

        soffice_path = self._get_soffice_path()
        if not soffice_path:
            raise UserError(_("Không tìm thấy LibreOffice (soffice) trên máy chủ để chuyển đổi PDF."))

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = os.path.join(tmp_dir, "input.docx")
            with open(input_path, 'wb') as f:
                f.write(docx_content)
            
            try:
                subprocess.run([
                    soffice_path,
                    '--headless',
                    '--convert-to', 'pdf',
                    '--outdir', tmp_dir,
                    input_path
                ], check=True, capture_output=True, timeout=30)
                
                pdf_path = os.path.join(tmp_dir, "input.pdf")
                if os.path.exists(pdf_path):
                    with open(pdf_path, 'rb') as f:
                        return f.read()
            except Exception as e:
                _logger.error("Lỗi khi gọi LibreOffice: %s", str(e))
                raise UserError(_("Lỗi trong quá trình chuyển đổi PDF: %s") % str(e))
        return None


class DlWoodSpecies(models.Model):
    _name = 'dl.wood.species'
    _description = 'Loài gỗ'
    _inherit = ['dl.wood.log.mixin']

    name = fields.Char(string='Tên loài', required=True)
    name_en = fields.Char(string='Tên tiếng Anh')
    name_sci = fields.Char(string='Tên khoa học')
    material_name = fields.Char(string='Tên nguyên liệu')
    code = fields.Char(string='Mã loài')
    wood_type = fields.Selection([
        ('wood', 'Gỗ'),
        ('firewood', 'Củi')
    ], string='Phân loại', default='wood', required=True)
    note = fields.Text(string='Ghi chú')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company)
    
    grade_ids = fields.One2many('dl.wood.species.grade', 'species_id', string='Phân loại')


class DlWoodSpeciesGrade(models.Model):
    _name = 'dl.wood.species.grade'
    _description = 'Phân loại chất lượng loài gỗ'

    species_id = fields.Many2one('dl.wood.species', string='Loài gỗ', ondelete='cascade')
    name = fields.Char(string='Tên phân loại', required=True)
    diameter_min = fields.Integer(string='Đường kính Min (cm)')
    diameter_max = fields.Integer(string='Đường kính Max (cm)')
    height = fields.Float(string='Chiều cao (m)')
    default_price = fields.Integer(string='Giá mặc định')
    note = fields.Char(string='Ghi chú')
    company_id = fields.Many2one('res.company', related='species_id.company_id', store=True, index=True)

    @api.depends('name', 'diameter_min', 'diameter_max', 'height')
    def _compute_display_name(self):
        for rec in self:
            # Format: Tên loại - (đường kính min - đường kính max) - chiều cao
            # Ví dụ: Loại A - (14-16) - 2,6
            diameter_str = f"({rec.diameter_min}-{rec.diameter_max})" if rec.diameter_min or rec.diameter_max else ""
            height_str = f"{rec.height:.1f}".replace('.', ',') if rec.height else ""
            
            parts = [rec.name]
            if diameter_str: parts.append(diameter_str)
            if height_str: parts.append(height_str)
            
            rec.display_name = " - ".join(parts)


class DlWoodDossier(models.Model):
    _name = 'dl.wood.dossier'
    _description = 'Hồ Sơ Gỗ (Nguồn khai thác)'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'dl.wood.log.mixin', 'dl.wood.pdf.mixin']
    _order = 'id desc'

    @api.model
    def _get_default_name(self):
        prefix = self.env.company.x_wood_prefix or "XX"
        # Đếm số lượng hồ sơ hiện có của công ty để cộng thêm 1
        count = self.search_count([('company_id', '=', self.env.company.id)])
        return f"{prefix}_HS_{(count + 1):04d}"

    name = fields.Char(string='Mã Hồ Sơ', required=True, copy=False, readonly=True, default=_get_default_name)
    x_dossier_name = fields.Char(string='Tên Hồ Sơ', help='Tên mô tả ngắn gọn cho bộ hồ sơ')
    partner_id = fields.Many2one(
        'res.partner', 
        string='Chủ Rừng / Nhà Cung Cấp', 
        required=True, 
        domain="[('active', '=', True), ('x_is_wood_supplier', '!=', False), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        check_company=True
    )
    partner_address = fields.Char(string='Địa chỉ', compute='_compute_partner_address', store=True, readonly=True)
    
    # Thông tin lâm nghiệp
    exploitation_location_id = fields.Many2one('dl.wood.exploitation.location', string='Địa bàn khai thác')
    x_mining_address = fields.Char(string='Địa chỉ khai thác (WoodPro)')
    x_area = fields.Float(string='Diện tích (ha)', digits=(16, 2))
    x_mining_method = fields.Selection([
        ('white', 'Khai thác trắng'),
        ('group', 'Khai thác theo đám')
    ], string='Phương thức khai thác', default='white')
    
    date_received = fields.Date(string='Ngày nhận hồ sơ', default=fields.Date.context_today)
    x_start_date = fields.Date(string='Từ ngày')
    x_end_date = fields.Date(string='Đến ngày')
    x_report_version_id = fields.Many2one('dl.wood.report.version', string='Phiên bản biểu mẫu', ondelete='restrict')
    x_exploitation_period_text = fields.Char(string='Thời gian khai thác (Văn bản)', compute='_compute_exploitation_period_text', store=False)
    x_addendum_num = fields.Char(string='Số phụ lục', compute='_compute_addendum_num', store=True, readonly=False)

    @api.depends('x_start_date', 'company_id.x_wood_prefix', 'partner_id.name')
    def _compute_addendum_num(self):
        for record in self:
            if not record.x_start_date or not record.partner_id:
                continue
            
            date_str = record.x_start_date.strftime('%d/%m/%Y')
            prefix = record.company_id.x_wood_prefix or "DL"
            
            # Lấy chữ cái viết tắt của chủ rừng (Không dấu)
            name_no_accent = no_accent_vietnamese(record.partner_id.name).replace('_', ' ')
            initials = "".join(word[0] for word in name_no_accent.split() if word).upper()
            
            record.x_addendum_num = f"{date_str}_{prefix}_{initials}"

            record.x_addendum_num = f"{date_str}_{prefix}_{initials}"
    
    # Thông tin Phương án (PAKT)
    x_pakt_date = fields.Date(string='Ngày lập PAKT')
    x_pakt_representative = fields.Char(string='Người đại diện')
    x_pakt_position = fields.Char(string='Chức vụ')

    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('exploiting', 'Đang khai thác'),
        ('summary', 'Tổng Kết'),
        ('confirmed', 'Xác Nhận')
    ], string='Trạng thái', default='draft', tracking=True)

    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company)
    x_woodpro_id = fields.Char(string='ID WoodPro', index=True)

    # Sản phẩm đại diện (để map với product_id của ledger)
    product_id = fields.Many2one('product.product', string='Sản phẩm đại diện', help='Dùng để map với Sổ cái (Ledger)')

    # Chi tiết loài gỗ và khối lượng theo hồ sơ
    line_ids = fields.One2many('dl.wood.dossier.line', 'dossier_id', string='Chi tiết loài gỗ')
    initial_qty = fields.Float(string='Tổng Khối Lượng (m³)', compute='_compute_initial_qty', store=True, digits=(16, 2))
    initial_wood_qty = fields.Float(string='Tổng Gỗ (m³)', compute='_compute_initial_qty', store=True, digits=(16, 2))
    initial_firewood_qty = fields.Float(string='Tổng Củi (m³)', compute='_compute_initial_qty', store=True, digits=(16, 2))
    
    total_wood_amount = fields.Integer(string='Tổng Tiền Gỗ', compute='_compute_amounts', store=True)
    total_firewood_amount = fields.Integer(string='Tổng Tiền Củi', compute='_compute_amounts', store=True)
    total_amount = fields.Integer(string='Tổng Cộng Thành Tiền', compute='_compute_amounts', store=True)

    # Tệp đính kèm
    x_internal_attachment_ids = fields.Many2many('ir.attachment', string='Tệp Đính Kèm (Hệ Thống)')
    attachment_ids = fields.One2many('dl.wood.dossier.attachment', 'dossier_id', string='Tệp đính kèm (WoodPro)')

    # Danh sách 8 tài liệu hệ thống cố định
    document_ids = fields.One2many('dl.wood.dossier.document', 'dossier_id', string='Tài liệu hệ thống')

    # -------------------------------------------------------------------------
    # Ledger Relation & Stock Calculation
    # -------------------------------------------------------------------------
    ledger_ids = fields.One2many('dl.dossier.ledger', 'dossier_id', string='Sổ Cái Biến Động')

    remaining_qty = fields.Float(string='Tồn Kho Thực Tế (m³)', compute='_compute_stock_quantities', store=True, digits=(16, 4))
    qty_reserved = fields.Float(string='Đang Giữ Đơn (m³)', compute='_compute_stock_quantities', store=True, digits=(16, 4))
    qty_available = fields.Float(string='Khả Dụng Để Bán (m³)', compute='_compute_stock_quantities', store=True, digits=(16, 4))

    @api.depends('line_ids.price_subtotal', 'line_ids.wood_type')
    def _compute_amounts(self):
        for dossier in self:
            wood_lines = dossier.line_ids.filtered(lambda l: l.wood_type == 'wood')
            firewood_lines = dossier.line_ids.filtered(lambda l: l.wood_type == 'firewood')
            
            dossier.total_wood_amount = sum(wood_lines.mapped('price_subtotal'))
            dossier.total_firewood_amount = sum(firewood_lines.mapped('price_subtotal'))
            dossier.total_amount = dossier.total_wood_amount + dossier.total_firewood_amount

    @api.depends('initial_qty', 'ledger_ids.actual_qty', 'ledger_ids.state')
    def _compute_stock_quantities(self):
        for dossier in self:
            done_lines = dossier.ledger_ids.filtered(lambda l: l.state == 'done')
            draft_lines = dossier.ledger_ids.filtered(lambda l: l.state == 'draft')
            
            dossier.remaining_qty = round(dossier.initial_qty + sum(done_lines.mapped('actual_qty')), 4)
            dossier.qty_reserved = round(abs(sum(draft_lines.mapped('actual_qty'))), 4)
            dossier.qty_available = round(dossier.remaining_qty - dossier.qty_reserved, 4)

    @api.model_create_multi
    def create(self, vals_list):
        records = super(DlWoodDossier, self).create(vals_list)
        for record in records:
            # Tự động tạo tài liệu mẫu khi tạo hồ sơ mới
            record._init_default_documents()
        return records

    @api.onchange('x_report_version_id')
    def _onchange_report_version_id(self):
        """Tự động nạp danh sách tài liệu khi đổi phiên bản"""
        if self.x_report_version_id:
            # Xóa các document cũ
            self.document_ids = [(5, 0, 0)]
            # Tạo mới dựa trên config của version (bao gồm cả các bản ghi không sử dụng)
            new_docs = []
            for config in self.x_report_version_id.template_config_ids:
                if not config.template_key:
                    continue
                new_docs.append((0, 0, {
                    'name': config.name,
                    'template_key': config.template_key,
                    'x_category': config.category,
                    'config_id': config.id,
                    'x_is_selected': config.is_enabled,
                    'is_enabled': config.is_enabled,
                    'sequence': config.sequence,
                }))
            self.document_ids = new_docs

    def action_refresh_documents(self):
        """Nút bấm thủ công để nạp lại danh sách tài liệu theo phiên bản hiện tại"""
        self.ensure_one()
        self._onchange_report_version_id()

    def _init_default_documents(self):
        """Khởi tạo danh sách tài liệu mặc định (sử dụng phiên bản mặc định)"""
        if not self.x_report_version_id:
            # Tìm phiên bản mặc định của công ty
            default_version = self.env['dl.wood.report.version'].search([
                ('company_id', '=', self.company_id.id)
            ], limit=1, order='id desc')
            if default_version:
                self.x_report_version_id = default_version
                self._onchange_report_version_id()

    @api.depends('partner_id.street', 'partner_id.city', 'partner_id.state_id')
    def _compute_partner_address(self):
        for record in self:
            addr = []
            if record.partner_id:
                p = record.partner_id
                if p.street: addr.append(p.street)
                if p.city: addr.append(p.city)
                if p.state_id: addr.append(p.state_id.name)
            record.partner_address = ", ".join(addr) if addr else ""

    @api.depends('line_ids.volume', 'line_ids.wood_type')
    def _compute_initial_qty(self):
        for record in self:
            record.initial_wood_qty = round(sum(record.line_ids.filtered(lambda l: l.wood_type == 'wood').mapped('volume')), 2)
            record.initial_firewood_qty = round(sum(record.line_ids.filtered(lambda l: l.wood_type == 'firewood').mapped('volume')), 2)
            record.initial_qty = round(record.initial_wood_qty + record.initial_firewood_qty, 2)

    # --- QUẢN LÝ TRẠNG THÁI (STATE MACHINE) ---
    def action_draft(self):
        self.write({'state': 'draft'})

    def action_exploiting(self):
        self.write({'state': 'exploiting'})

    def action_summary(self):
        self.write({'state': 'summary'})

    def action_confirm(self):
        for record in self:
            if not record.line_ids:
                raise UserError(_("Vui lòng nhập chi tiết loại gỗ trước khi xác nhận."))
        self.write({'state': 'confirmed'})

    # --- XUẤT FILE WORD (Cơ chế render trực tiếp không lưu file) ---
    def _prepare_pakt_context(self):
        """Chuẩn bị dữ liệu để điền vào template PAKT theo chuẩn Jinja2 {{ }}"""
        self.ensure_one()
        partner = self.partner_id
        
        def format_date(d):
            return d.strftime('%d/%m/%Y') if d else ""

        mining_method_map = {
            'white': _('Khai thác trắng toàn bộ'),
            'group': _('Khai thác theo đám')
        }

        total_volume = self.initial_wood_qty

        context = {
            'forestOwnerName': partner.name or "",
            'forestOwnerAddr': self.partner_address or "",
            'forestCity': partner.city or "",
            'foestOwnerCccd': partner.x_cccd or "",
            'cccdDate': format_date(partner.x_cccd_date),
            'cccdPlace': partner.x_cccd_place or "",
            'forestOwnerPhoneNumber': partner.phone or "",
            'miningArea': self.x_area or 0.0,
            'forestAddr': self.exploitation_location_id.name or self.partner_address or "",
            'typeMining': mining_method_map.get(self.x_mining_method, ""),
            'projectedMiningOutput': f"{total_volume:,.2f} m3".replace(',', '.'),
            'miningFromDate': date_to_vietnamese_text(self.x_start_date),
            'miningFromdate': date_to_vietnamese_text(self.x_start_date),
            'miningToDate': date_to_vietnamese_text(self.x_end_date),
            'representative': self.x_pakt_representative or "",
            'position': self.x_pakt_position or "",
            'companyName': self.company_id.name or "",
            'table_rows': [{
                'stt': idx,
                'species': line.species_id.name or "",
                'name_en': line.name_en or "",
                'grade': line.grade_id.name or "",
                'quantity': line.quantity or 0,
                'volume': f"{line.volume:,.2f}".replace(',', '.'),
                'diameter': line.diameter_display or "",
                'height': line.height_display or "",
                'price_subtotal': f"{line.price_subtotal:,}".replace(',', '.'),
                'note': line.note or ""
            } for idx, line in enumerate(self.line_ids, 1)]
        }
        return context

    def _render_docx(self, template_key):
        """Render file docx từ template (Binary hoặc Disk)"""
        self.ensure_one()
        if not DocxTemplate:
            raise UserError(_("Thư viện 'docxtpl' chưa được cài đặt."))

        # 1. Tìm bản ghi document tương ứng trong hồ sơ
        doc_record = self.document_ids.filtered(lambda d: d.template_key == template_key)
        
        # 2. Ưu tiên lấy template từ cấu hình người dùng tải lên (Binary)
        if doc_record and doc_record[0].config_id and doc_record[0].config_id.template_file:
            template_source = io.BytesIO(base64.b64decode(doc_record[0].config_id.template_file))
        else:
            # 3. Fallback lấy template mặc định từ ổ đĩa
            template_filename = f"TEMPLATE_{template_key.upper()}.docx"
            try:
                template_source = tools.file_path(f'dl_wood_traceability/static/TEMPLATES/{template_filename}')
            except FileNotFoundError:
                # Fallback cuối cùng về PAKT
                template_source = tools.file_path('dl_wood_traceability/static/TEMPLATES/TEMPLATE_PAKT.docx')

        # 4. Chuẩn bị context và render
        context = self._prepare_pakt_context()
        try:
            doc = DocxTemplate(template_source)
            doc.render(context)
            output = io.BytesIO()
            doc.save(output)
            return output.getvalue()
        except Exception as e:
            _logger.error("Lỗi khi render %s: %s", template_key, e)
            raise UserError(_("Lỗi định dạng hoặc không thể đọc template %s: %s") % (template_key, str(e)))

    def action_export_pakt_docx(self):
        """Nút bấm nhanh cho PAKT (Giữ lại để tương thích view cũ nếu cần)"""
        return self._action_download_template('pakt')

    def action_download_ptkt(self): return self._action_download_template('ptkt')
    def action_download_hdsg(self): return self._action_download_template('hdsg')
    def action_download_bkls(self): return self._action_download_template('bkls')
    def action_download_ddnx(self): return self._action_download_template('ddnx')
    def action_download_bbxm(self): return self._action_download_template('bbxm')
    def action_download_cnbk(self): return self._action_download_template('cnbk')
    def action_download_pnk(self): return self._action_download_template('pnk')
    def action_download_bbbg(self): return self._action_download_template('bbbg')
    def action_download_gbn(self): return self._action_download_template('gbn')

    def action_download_zip(self):
        """Tải các tài liệu đã chọn dưới dạng file nén ZIP"""
        selected_docs = self.document_ids.filtered(lambda d: d.x_is_selected)
        if not selected_docs:
            raise UserError(_("Vui lòng chọn ít nhất một tài liệu để tải ZIP."))
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/dl_wood/download_zip/{self.id}',
            'target': 'self',
        }

    def action_select_all_exploitation(self):
        self.document_ids.filtered(lambda d: d.x_category == 'exploitation').write({'x_is_selected': True})
    
    def action_deselect_all_exploitation(self):
        self.document_ids.filtered(lambda d: d.x_category == 'exploitation').write({'x_is_selected': False})

    def action_select_all_logistics(self):
        self.document_ids.filtered(lambda d: d.x_category == 'logistics').write({'x_is_selected': True})

    def action_deselect_all_logistics(self):
        self.document_ids.filtered(lambda d: d.x_category == 'logistics').write({'x_is_selected': False})

    def _action_download_template(self, template_key):
        return {
            'type': 'ir.actions.act_url',
            'url': f'/dl_wood/render_docx/{self.id}/{template_key}',
            'target': 'self',
        }

    def get_export_filename(self, template_key):
        """Tạo tên file theo format: Tiền tố_Tên không dấu_Mã hồ sơ_Ngày tải.docx"""
        self.ensure_one()
        prefix = self.company_id.x_wood_prefix or "DL"
        
        # Lấy tên hiển thị của tài liệu từ document_ids
        doc = self.document_ids.filtered(lambda d: d.template_key == template_key)
        raw_name = doc[0].name if doc else template_key.upper()
        # Loại bỏ tiền tố số (1., 2...) nếu có
        if '. ' in raw_name:
            raw_name = raw_name.split('. ', 1)[1]
            
        clean_name = no_accent_vietnamese(raw_name)
        date_str = fields.Date.today().strftime('%d%m%Y')
        
        return f"{prefix}_{clean_name}_{self.name}_{date_str}.docx"


class DlWoodDossierDocument(models.Model):
    _name = 'dl.wood.dossier.document'
    _description = 'Tài liệu hệ thống của hồ sơ gỗ'
    _order = 'sequence, id'

    dossier_id = fields.Many2one('dl.wood.dossier', string='Hồ Sơ Gỗ', ondelete='cascade')
    sequence = fields.Integer(string='STT', default=10)
    name = fields.Char(string='Tên tài liệu', required=True)
    template_key = fields.Char(string='Mã template')
    is_enabled = fields.Boolean(string='Đang dùng', related='config_id.is_enabled', readonly=True)
    config_id = fields.Many2one('dl.wood.report.template.config', string='Cấu hình mẫu', ondelete='set null')
    x_category = fields.Selection([
        ('exploitation', 'Hồ sơ khai thác'),
        ('logistics', 'Hồ sơ vận chuyển/Bàn giao')
    ], string='Phân loại', related='config_id.category', readonly=True)
    x_is_selected = fields.Boolean(string='Chọn', default=True)
    company_id = fields.Many2one('res.company', related='dossier_id.company_id', store=True, index=True)
    
    def action_download(self):
        """Trả về URL để controller render và tải file về ngay lập tức"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/dl_wood/render_docx/{self.dossier_id.id}/{self.template_key}',
            'target': 'self',
        }

    def action_preview_pdf(self):
        """Mở tab mới để xem trước bản PDF"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/dl_wood/preview_pdf/{self.dossier_id.id}/{self.template_key}',
            'target': 'new',
        }


class DlWoodDossierLine(models.Model):
    _name = 'dl.wood.dossier.line'
    _description = 'Chi tiết loài gỗ trong hồ sơ'

    dossier_id = fields.Many2one('dl.wood.dossier', string='Hồ Sơ Gỗ', ondelete='cascade')
    partner_id = fields.Many2one('res.partner', related='dossier_id.partner_id', store=True, index=True)
    company_id = fields.Many2one('res.company', related='dossier_id.company_id', store=True, index=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    
    species_id = fields.Many2one('dl.wood.species', string='Loài gỗ', required=True)
    grade_id = fields.Many2one('dl.wood.species.grade', string='Phân loại', domain="[('species_id', '=', species_id)]")
    name = fields.Char(string='Tên loài', related='species_id.name', readonly=True)
    wood_type = fields.Selection(related='species_id.wood_type', store=True, readonly=True)
    name_en = fields.Char(string='Tên tiếng Anh', related='species_id.name_en', readonly=True)
    name_sci = fields.Char(string='Tên khoa học', related='species_id.name_sci', readonly=True)
    
    quantity = fields.Integer(string='Số lượng (Cây)')
    volume = fields.Float(string='Khối lượng (m³)', required=True, digits=(16, 2))
    price_unit = fields.Integer(string='Đơn giá')
    price_subtotal = fields.Integer(string='Thành tiền', compute='_compute_price_subtotal', store=True)

    @api.depends('volume', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = int(round(line.volume * line.price_unit))

    @api.onchange('species_id')
    def _onchange_species_id(self):
        if self.species_id:
            first_grade = self.env['dl.wood.species.grade'].search([('species_id', '=', self.species_id.id)], limit=1)
            if first_grade:
                self.grade_id = first_grade
                # Gán luôn các giá trị định mức
                self.diameter_min = first_grade.diameter_min
                self.diameter_max = first_grade.diameter_max
                self.height = first_grade.height
                self.price_unit = first_grade.default_price

    @api.onchange('grade_id')
    def _onchange_grade_id(self):
        if self.grade_id:
            self.diameter_min = self.grade_id.diameter_min
            self.diameter_max = self.grade_id.diameter_max
            self.height = self.grade_id.height
            self.price_unit = self.grade_id.default_price

    @api.onchange('volume', 'diameter_min', 'diameter_max', 'height')
    def _onchange_calculate_quantity(self):
        """
        Tự động tính số lượng dựa trên khối lượng và kích thước.
        Công thức: Số lượng = Khối lượng / (Diện tích mặt cắt * Chiều cao)
        Diện tích mặt cắt = (D_tb/100)^2 * 3.14159 / 4
        """
        for line in self:
            if line.volume and (line.diameter_min or line.diameter_max) and line.height:
                # Tính đường kính trung bình (cm)
                d_avg = (line.diameter_min + line.diameter_max) / 2.0
                if d_avg > 0:
                    # Tính thể tích của 1 khúc gỗ (m3)
                    # Thể tích = (D/100)^2 * (Pi/4) * H
                    # Pi/4 xấp xỉ 0.785398
                    vol_per_piece = ((d_avg / 100.0) ** 2) * 0.785398 * line.height
                    
                    if vol_per_piece > 0:
                        # Tính số lượng và làm tròn
                        line.quantity = int(round(line.volume / vol_per_piece))
    diameter_min = fields.Integer(string='ĐK Min (cm)')
    diameter_max = fields.Integer(string='ĐK Max (cm)')
    diameter_display = fields.Char(string='ĐK (cm)', compute='_compute_diameter_display', help='Hiển thị dạng Min-Max')
    height = fields.Float(string='Cao (m)')
    height_display = fields.Char(string='Cao (m)', compute='_compute_height_display')
    avg_diameter = fields.Float(string='ĐK Trung bình (cm)')
    avg_height = fields.Float(string='Cao Trung bình (m)')

    @api.depends('diameter_min', 'diameter_max')
    def _compute_diameter_display(self):
        for line in self:
            if line.diameter_min or line.diameter_max:
                if line.diameter_min == line.diameter_max:
                    line.diameter_display = str(line.diameter_min)
                else:
                    line.diameter_display = f"{line.diameter_min}-{line.diameter_max}"
            else:
                line.diameter_display = ""

    @api.depends('height')
    def _compute_height_display(self):
        for line in self:
            line.height_display = f"{line.height:.1f}".replace('.', ',') if line.height else ""
    
    note = fields.Char(string='Ghi chú')
    x_woodpro_id = fields.Char(string='ID WoodPro')


class DlWoodDossierAttachment(models.Model):
    _name = 'dl.wood.dossier.attachment'
    _description = 'Tệp đính kèm từ WoodPro'

    dossier_id = fields.Many2one('dl.wood.dossier', string='Hồ Sơ Gỗ', ondelete='cascade')
    name = fields.Char(string='Tên tệp', required=True)
    x_woodpro_id = fields.Char(string='WoodPro ID')
    status = fields.Char(string='Trạng thái')
    url = fields.Char(string='Link tải')
    file_type = fields.Selection([
        ('forest_exploitation', 'Phiếu thông tin khai thác'),
        ('hsg', 'Hợp đồng/Hồ sơ'),
        ('manifest', 'Bảng kê lâm sản'),
    ], string='Loại tệp')
    company_id = fields.Many2one('res.company', related='dossier_id.company_id', store=True, index=True)

    def action_download_file(self):
        self.ensure_one()
        if not self.url:
            raise UserError(_("Tệp này không có đường dẫn tải về."))
        return {
            'type': 'ir.actions.act_url',
            'url': self.url,
            'target': 'new',
        }


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def download_attachment(self):
        """Hỗ trợ tải file nhanh từ giao diện List view"""
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.id}?download=true',
            'target': 'self',
        }


class DlWoodReportVersion(models.Model):
    _name = 'dl.wood.report.version'
    _description = 'Phiên bản biểu mẫu báo cáo'
    _order = 'id desc'

    name = fields.Char(string='Tên phiên bản', required=True)
    code = fields.Char(string='Mã phiên bản', required=True, help="Ví dụ: v2025, v2026")
    active = fields.Boolean(string='Đang sử dụng', default=True)
    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company)
    template_config_ids = fields.One2many('dl.wood.report.template.config', 'version_id', string='Cấu hình mẫu tài liệu')


class DlWoodReportTemplateConfig(models.Model):
    _name = 'dl.wood.report.template.config'
    _description = 'Cấu hình mẫu tài liệu'
    _order = 'sequence, id'

    version_id = fields.Many2one('dl.wood.report.version', string='Phiên bản', ondelete='cascade')
    sequence = fields.Integer(string='STT', default=10)
    name = fields.Char(string='Tên tài liệu', required=True)
    template_key = fields.Char(string='Mã kỹ thuật', compute='_compute_template_key', store=True, readonly=False, help="Dùng để định danh mẫu trong code")
    is_enabled = fields.Boolean(string='Sử dụng', default=True)
    category = fields.Selection([
        ('exploitation', 'Hồ sơ khai thác'),
        ('logistics', 'Hồ sơ vận chuyển/Bàn giao')
    ], string='Phân loại', default='exploitation')
    template_file = fields.Binary(string='File mẫu (.docx)')
    template_filename = fields.Char(string='Tên file mẫu')

    @api.depends('name')
    def _compute_template_key(self):
        for rec in self:
            if rec.name:
                # Loại bỏ số thứ tự ở đầu nếu có (ví dụ: "1. Tên file")
                raw_name = rec.name
                if '. ' in raw_name:
                    raw_name = raw_name.split('. ', 1)[1]
                
                clean = no_accent_vietnamese(raw_name).lower()
                # Hàm no_accent_vietnamese đã xử lý thay thế khoảng trắng bằng '_'
                # Chúng ta chỉ cần đảm bảo nó ở dạng chữ thường
                rec.template_key = clean
            else:
                rec.template_key = False
