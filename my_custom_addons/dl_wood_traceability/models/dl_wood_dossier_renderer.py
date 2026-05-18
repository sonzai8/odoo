# -*- coding: utf-8 -*-
"""
dl_wood_dossier_renderer.py — Tầng render tài liệu Word (.docx) cho Hồ sơ Gỗ.

Mỗi loại biểu mẫu có hàm chuẩn bị context riêng biệt để dễ theo dõi, debug
và tránh gọi nhầm dữ liệu giữa các tài liệu khác nhau.

Quy tắc:
  - Thêm template mới: thêm hàm _prepare_<key>_context() + 1 dòng vào TEMPLATE_CONTEXT_MAP.
  - Renderer này KHÔNG import UserError — lỗi sẽ bubble up về dl_wood_dossier.py để bọc lại.
"""
import io
import re
import logging

try:
    from docxtpl import DocxTemplate
except ImportError:
    DocxTemplate = None

from odoo import _

_logger = logging.getLogger(__name__)


# =============================================================================
# HELPER FUNCTIONS (Di chuyển từ dl_wood_dossier.py để dùng chung)
# =============================================================================

def date_to_vietnamese_text(d):
    """Chuyển đổi date object → chuỗi tiếng Việt: 'ngày 06 tháng 04 năm 2026'"""
    if not d:
        return ""
    return f"ngày {d.day:02d} tháng {d.month:02d} năm {d.year}"


def no_accent_vietnamese(s):
    """Chuyển đổi tiếng Việt có dấu → không dấu, chuẩn hoá thành chữ HOA cho tên file"""
    if not s:
        return ""
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
    s = re.sub(r'[^a-z0-9\s]', '', s)
    s = re.sub(r'\s+', '_', s.strip())
    return s.upper()


def number_to_vietnamese_words(num):
    """
    Chuyển đổi một số nguyên thành chữ tiếng Việt (ví dụ: 123 -> 'Một trăm hai mươi ba').
    """
    if num is None:
        return ""
    try:
        num = int(round(float(num)))
    except (ValueError, TypeError):
        return ""

    if num == 0:
        return "Không"

    negative = False
    if num < 0:
        negative = True
        num = abs(num)

    units = ["", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
    
    def read_block_3(n, show_zero_hundred=False):
        hundreds = n // 100
        tens = (n % 100) // 10
        ones = n % 10
        
        res = []
        if hundreds > 0 or show_zero_hundred:
            res.append(units[hundreds] + " trăm")
            
        if tens > 0:
            if tens == 1:
                res.append("mười")
            else:
                res.append(units[tens] + " mươi")
        elif (hundreds > 0 or show_zero_hundred) and ones > 0:
            res.append("lẻ")
            
        if ones > 0:
            if ones == 1 and tens > 1:
                res.append("mốt")
            elif ones == 5 and tens > 0:
                res.append("lăm")
            else:
                res.append(units[ones])
        return " ".join(res)

    chunks = []
    temp = num
    while temp > 0:
        chunks.append(temp % 1000)
        temp //= 1000

    scales = ["", "nghìn", "triệu", "tỷ", "nghìn tỷ", "triệu tỷ"]
    res_blocks = []
    
    for idx, block in enumerate(chunks):
        if block == 0:
            continue
        show_zero_hundred = (idx < len(chunks) - 1)
        block_text = read_block_3(block, show_zero_hundred)
        if block_text:
            scale = scales[idx]
            if scale:
                res_blocks.append(block_text + " " + scale)
            else:
                res_blocks.append(block_text)
                
    result = " ".join(reversed(res_blocks)).strip()
    result = re.sub(r'\s+', ' ', result)
    
    if negative:
        result = "âm " + result
        
    return result[0].upper() + result[1:] if result else ""


# =============================================================================
# MAIN RENDERER CLASS
# =============================================================================

class DossierDocxRenderer:
    """
    Renderer tài liệu Word cho Hồ sơ Gỗ (dl.wood.dossier).

    Cách dùng:
        renderer = DossierDocxRenderer(dossier_record)
        file_bytes = renderer.render('hop_dong_hsg', template_source)

    Để thêm template mới:
        1. Thêm hàm: def _prepare_<key>_context(self): ...
        2. Thêm 1 dòng vào TEMPLATE_CONTEXT_MAP.
    """

    # -------------------------------------------------------------------------
    # Bảng ánh xạ: template_key → tên hàm _prepare_*_context
    # -------------------------------------------------------------------------
    TEMPLATE_CONTEXT_MAP = {
        # Hợp đồng hồ sơ nguồn gốc
        'hop_dong_hsg':             '_prepare_hop_dong_hsg_context',
        'hdhsg':                    '_prepare_hop_dong_hsg_context',
        'hdsg':                     '_prepare_hop_dong_hsg_context',
        'hop_dong_ho_so_nguon_goc': '_prepare_hop_dong_hsg_context',
        
        # Phương án khai thác
        'pakt':                     '_prepare_pakt_context',
        'phuong_an_khai_thac':      '_prepare_pakt_context',
        
        # Phiếu thông tin khai thác
        'ptkt':                     '_prepare_ptkt_context',
        'phieu_thong_tin_khai_thac': '_prepare_ptkt_context',
        
        # Bảng kê lâm sản
        'bkls':                     '_prepare_bkls_context',
        'ban_ke_lam_san':           '_prepare_bkls_context',
        'bang_ke_lam_san':          '_prepare_bkls_context',
        
        # Đơn đề nghị xác nhận
        'ddnx':                     '_prepare_ddnx_context',
        'don_de_nghi_xac_nhan':     '_prepare_ddnx_context',
        
        # Biên bản xác minh
        'bbxm':                     '_prepare_bbxm_context',
        'bien_ban_xac_minh':        '_prepare_bbxm_context',
        
        # Các mẫu phụ
        'cnbk':                     '_prepare_cnbk_context',
        'cam_ket_nguon_goc':        '_prepare_cnbk_context',
        'pnk':                      '_prepare_pnk_context',
        'phieu_nhap_kho':           '_prepare_pnk_context',
        'bbbg':                     '_prepare_bbbg_context',
        'bien_ban_ban_giao':        '_prepare_bbbg_context',
        'gbn':                      '_prepare_gbn_context',
        'giay_ban_no':              '_prepare_gbn_context',
    }

    def __init__(self, dossier):
        """
        :param dossier: Bản ghi dl.wood.dossier (Odoo recordset, ensure_one() đã gọi trước)
        """
        self.dossier = dossier

    # -------------------------------------------------------------------------
    # ENTRY POINTS
    # -------------------------------------------------------------------------

    def get_context(self, template_key):
        """
        Định tuyến template_key → đúng hàm _prepare_*_context().
        Raise ValueError rõ ràng nếu template_key chưa được đăng ký.
        """
        method_name = self.TEMPLATE_CONTEXT_MAP.get(template_key)
        if not method_name:
            valid_keys = ', '.join(self.TEMPLATE_CONTEXT_MAP.keys())
            raise ValueError(
                f"Không tìm thấy hàm chuẩn bị context cho template_key='{template_key}'. "
                f"Các key hợp lệ: {valid_keys}"
            )
        _logger.info(
            "[DossierDocxRenderer] template_key='%s' → %s()",
            template_key, method_name
        )
        return getattr(self, method_name)()

    def render(self, template_key, template_source):
        """
        Render file Word từ template_source với context tương ứng template_key.

        :param template_key: Mã template (ví dụ: 'hop_dong_hsg', 'pakt')
        :param template_source: BytesIO hoặc đường dẫn file .docx
        :return: bytes — nội dung file .docx đã điền dữ liệu
        """
        if not DocxTemplate:
            raise ImportError("Thư viện 'docxtpl' chưa được cài đặt trên máy chủ.")

        context = self.get_context(template_key)
        doc = DocxTemplate(template_source)
        doc.render(context)
        output = io.BytesIO()
        doc.save(output)
        return output.getvalue()

    # =========================================================================
    # PRIVATE HELPERS — Dùng chung giữa các hàm prepare_context
    # =========================================================================

    def _format_date(self, d):
        """Định dạng date object → chuỗi 'dd/mm/yyyy'"""
        return d.strftime('%d/%m/%Y') if d else ""

    def _build_table_rows(self):
        """
        Xây dựng danh sách hàng bảng (table_rows) dùng chung.
        Mỗi phần tử dict tương ứng 1 hàng trong bảng Word.
        """
        rows = []
        for idx, line in enumerate(self.dossier.line_ids, 1):
            rows.append({
                'stt':           idx,
                'idx':           idx,
                'species':       line.species_id.name or "",
                'species_name':  line.species_id.name or "",
                'name_en':       line.name_en or "",
                'grade':         line.grade_id.name or "",
                'unit':          'm3' if line.wood_type == 'wood' else 'củi',
                'quantity': (
                    f"{int(round(line.volume)):,}".replace(',', '.')
                    if line.wood_type == 'wood' else f"{int(line.quantity or 0):,}".replace(',', '.')
                ),
                'volume':        f"{int(round(line.volume)):,}".replace(',', '.'),
                'diameter':      line.diameter_display or "",
                'height':        line.height_display or "",
                'price_unit':    f"{line.price_unit:,}".replace(',', '.'),
                'price_subtotal': f"{int(line.price_subtotal):,}".replace(',', '.'),
                'note':          line.note or "",
            })
        return rows

    def _get_owner_info(self):
        """Trích xuất thông tin chủ rừng (bên bán) thành dict."""
        d = self.dossier
        p = d.partner_id
        owner_rep = d.x_owner_representative or p.name or ""
        owner_pos = d.x_owner_position or "Chủ rừng"
        return {
            'owner_name':            p.name or "",
            'owner_address':         d.partner_address or "",
            'owner_cccd':            p.x_cccd or "",
            'owner_cccd_date_issue': self._format_date(p.x_cccd_date),
            'owner_cccd_place_issue': p.x_cccd_place or "",
            'owner_representative':  owner_rep,
            'owner_position':        owner_pos,
            'owner_positon':         owner_pos,   # dự phòng lỗi gõ phím trong template cũ
            'owner_pos':             owner_pos,
        }

    def _get_company_info(self):
        """Trích xuất thông tin công ty (bên mua) thành dict."""
        c = self.dossier.company_id
        rep  = c.x_representative or ""
        pos  = c.x_representative_position or ""
        return {
            'company_name':           c.name or "",
            'company_address':        c.street or "",
            'company_tax_number':     c.vat or "",
            'company_representative': rep,
            'company_ representative': rep,   # dự phòng lỗi gõ phím trong template cũ
            'representative_position': pos,
            'representative':         rep,
            'position':               pos,
            'companyName':            c.name or "",
        }

    # =========================================================================
    # CONTEXT METHODS — Mỗi template có hàm riêng biệt
    # =========================================================================

    def _prepare_hop_dong_hsg_context(self):
        """
        Chuẩn bị dữ liệu cho Hợp đồng mua bán gỗ (HDSG / hop_dong_hsg).

        Biến chính trong template:
          - company_name, company_address, company_representative, representative_position
          - owner_name, owner_cccd, owner_cccd_date_issue, owner_representative
          - date_of_hd  (ngày ký hợp đồng, dạng chữ tiếng Việt)
          - table_rows  (bảng hàng hóa động: idx, species_name, unit, quantity, price_unit, price_subtotal)
          - total_quantity, price_total
        """
        self.dossier.ensure_one()
        d = self.dossier

        # Debug log để theo dõi dữ liệu điền vào template
        _logger.info("=== HDSG DEBUG CONTEXT LOG ===")
        _logger.info("Dossier Name: %s", d.name)
        _logger.info("Line ids: %s", d.line_ids)
        for idx, line in enumerate(d.line_ids, 1):
            _logger.info(
                "Line %d: species=%s, volume=%f, qty=%f",
                idx, line.species_id.name, line.volume, line.quantity
            )
        _logger.info("=== END HDSG DEBUG LOG ===")

        line_ids = d.line_ids
        has_wood = any(l.wood_type == 'wood' for l in line_ids)
        main_species = ", ".join(
            list(set(line_ids.filtered(lambda l: l.species_id).mapped('species_id.name')))
        ) if line_ids else ""
        main_unit = 'm³' if has_wood else 'củi'
        main_qty_val = (
            sum(line_ids.mapped('volume')) if has_wood
            else sum(line_ids.mapped('quantity'))
        )
        main_qty = f"{int(round(main_qty_val)):,}".replace(',', '.')

        context = {
            **self._get_company_info(),
            **self._get_owner_info(),
            'date_of_hd':       date_to_vietnamese_text(d.x_contract_date),
            'total_quantity':   f"{int(round(d.initial_qty)):,}".replace(',', '.'),
            'price_total':      f"{int(d.total_amount):,}".replace(',', '.'),
            # Biến bổ trợ cho bảng không dùng vòng lặp
            'main_species_name': main_species,
            'main_unit_name':    main_unit,
            'main_quantity_val': main_qty,
            # Bảng hàng hóa động
            'table_rows':       self._build_table_rows(),
        }
        return context

    def _prepare_pakt_context(self):
        """
        Chuẩn bị dữ liệu cho Phương án khai thác (PAKT).

        Biến chính trong template:
          - forestOwnerName, forestOwnerAddr, foestOwnerCccd, cccdDate, cccdPlace
          - miningArea, forestAddr, typeMining, projectedMiningOutput
          - miningFromDate, miningToDate
          - representative, position, companyName
          - table_rows  (bảng loài gỗ)
        """
        self.dossier.ensure_one()
        d = self.dossier
        p = d.partner_id

        mining_method_map = {
            'white': _('Khai thác trắng toàn bộ'),
            'group': _('Khai thác theo đám'),
        }
        c_rep = d.company_id.x_representative or ""
        c_pos = d.company_id.x_representative_position or ""

        context = {
            # Thông tin chủ rừng
            'forestOwnerName':        p.name or "",
            'forestOwnerAddr':        d.partner_address or "",
            'forestCity':             p.city or "",
            'foestOwnerCccd':         p.x_cccd or "",
            'cccdDate':               self._format_date(p.x_cccd_date),
            'cccdPlace':              p.x_cccd_place or "",
            'forestOwnerPhoneNumber': p.phone or "",
            # Thông tin khai thác
            'miningArea':             d.x_area or 0.0,
            'forestAddr':             d.exploitation_location_id.name or d.partner_address or "",
            'typeMining':             mining_method_map.get(d.x_mining_method, ""),
            'projectedMiningOutput':  f"{int(round(d.initial_wood_qty)):,} m3".replace(',', '.'),
            # Thời gian khai thác
            'miningFromDate':         date_to_vietnamese_text(d.x_start_date),
            'miningFromdate':         date_to_vietnamese_text(d.x_start_date),  # dự phòng
            'miningToDate':           date_to_vietnamese_text(d.x_end_date),
            # Đại diện công ty
            'representative':         c_rep or d.x_pakt_representative or "",
            'position':               c_pos or d.x_pakt_position or "",
            'companyName':            d.company_id.name or "",
            # Bảng loài gỗ
            'table_rows':             self._build_table_rows(),
        }
        return context

    # -------------------------------------------------------------------------
    # SKELETON METHODS — Bổ sung biến riêng khi có nhu cầu thực tế
    # -------------------------------------------------------------------------

    def _prepare_ptkt_context(self):
        """[SKELETON] Phương tiện khai thác (PTKT). TODO: bổ sung biến riêng."""
        _logger.info("[Renderer] _prepare_ptkt_context — tạm dùng context PAKT")
        return self._prepare_pakt_context()

    def _prepare_bkls_context(self):
        """
        Chuẩn bị dữ liệu cho Bảng kê lâm sản (BKLS / bang_ke_lam_san).

        Các biến chính trong template:
          - company_name, company_address, company_tax_number
          - forest_owner_name, forest_owner_address, forest_owner_cccd (Đã sửa chính tả)
          - exploitation_address, exploitation_count_day
          - vietnamese_exploitation_from_date, vietnamese_exploitation_to_date
          - diameter_min, diameter_max (Đã sửa chính tả)
          - species_name, species_type, species_volume, firewood_quantity
          - firewood_volume, vietnamese_firewood_volume, vietnamese_firewood_quantity
          - total_quantity, total_volume, quantity
          - vietnamese_quantity, vietnamese_volume
          - table_rows (idx, species_name, name_sci, name_en, type, height, volume, quantity)
        """
        self.dossier.ensure_one()
        d = self.dossier
        p = d.partner_id
        
        company_info = self._get_company_info()
        owner_info = self._get_owner_info()
        
        # 1. Tính thời gian vận chuyển/khai thác
        count_days = 0
        if d.x_start_date and d.x_end_date:
            count_days = (d.x_end_date - d.x_start_date).days + 1
            
        # 2. Phân nhóm lâm sản (Gỗ vs Củi)
        line_ids = d.line_ids
        wood_lines = line_ids.filtered(lambda l: l.wood_type == 'wood')
        firewood_lines = line_ids.filtered(lambda l: l.wood_type == 'firewood')
        
        main_species = ", ".join(list(set(line_ids.filtered(lambda l: l.species_id).mapped('species_id.name')))) if line_ids else ""
        
        # Tổng hợp nhóm loài dựa trên cấu hình x_species_group mới
        groups = []
        for line in line_ids:
            val = line.species_id.x_species_group or 'common'
            label = {
                'common': 'Thông thường',
                'precious': 'Danh mục loài nguy cấp, quý, hiếm',
                'cites': 'Phụ lục CITES'
            }.get(val, 'Thông thường')
            groups.append(label)
        main_type = ", ".join(list(set(groups))) if groups else "Thông thường"
        
        # Tính cực trị đường kính
        dia_min = min(line_ids.mapped('diameter_min')) if line_ids and any(line_ids.mapped('diameter_min')) else 0
        dia_max = max(line_ids.mapped('diameter_max')) if line_ids and any(line_ids.mapped('diameter_max')) else 0
        
        # Tính toán sản lượng dạng số nguyên
        total_vol = sum(line_ids.mapped('volume'))
        total_qty = sum(line_ids.mapped('quantity'))
        
        wood_vol = sum(wood_lines.mapped('volume'))
        wood_qty = sum(wood_lines.mapped('quantity'))
        
        firewood_vol = sum(firewood_lines.mapped('volume'))
        firewood_qty = sum(firewood_lines.mapped('quantity'))
        
        # 3. Xây dựng danh sách hàng bảng chi tiết
        bkls_rows = []
        for idx, line in enumerate(line_ids, 1):
            val = line.species_id.x_species_group or 'common'
            group_label = {
                'common': 'Thông thường',
                'precious': 'Danh mục loài nguy cấp, quý, hiếm',
                'cites': 'Phụ lục CITES'
            }.get(val, 'Thông thường')

            bkls_rows.append({
                'idx':           idx,
                'stt':           idx,
                'species_name':  line.species_id.name or "",
                'name_sci':      line.name_sci or "",
                'name_en':       line.name_en or "",
                'type':          group_label,
                'height':        line.height_display or "",
                'diameter':      line.diameter_display or "",
                'volume':        f"{int(round(line.volume)):,}".replace(',', '.'),
                'quantity':      f"{int(line.quantity or 0):,}".replace(',', '.'),
            })
            
        context = {
            # Bên mua
            'company_name':           company_info.get('company_name', ''),
            'company_address':        company_info.get('company_address', ''),
            'company_tax_number':     company_info.get('company_tax_number', ''),
            
            # Chủ rừng (Bên bán - có cả phương án dự phòng lỗi chính tả cũ)
            'forest_owner_name':      owner_info.get('owner_name', ''),
            'forest_owner_address':   owner_info.get('owner_address', ''),
            'forset_owner_address':   owner_info.get('owner_address', ''), # dự phòng lỗi chính tả cũ
            'forest_owner_cccd':      owner_info.get('owner_cccd', ''),
            'forset_owner_cccd':      owner_info.get('owner_cccd', ''), # dự phòng lỗi chính tả cũ
            
            # Địa điểm & Thời gian
            'exploitation_address':   d.exploitation_location_id.name or d.partner_address or "",
            'exploitation_count_day': count_days,
            'vietnamese_exploitation_from_date': date_to_vietnamese_text(d.x_start_date),
            'vietnamese_exploitation_to_date':   date_to_vietnamese_text(d.x_end_date),
            
            # Đường kính cực trị (hỗ trợ cả biến đã sửa và biến lỗi chính tả cũ)
            'diameter_min':           dia_min,
            'diameter_max':           dia_max,
            'diametter_max':          dia_max, # dự phòng lỗi chính tả cũ
            
            # Nhóm loài & Loại lâm sản
            'species_name':           main_species,
            'species_type':           main_type,
            'species_volume':         f"{int(round(wood_vol)):,}".replace(',', '.'),
            'firewood_quantity':      f"{int(firewood_qty):,}".replace(',', '.'),
            'firewood_volume':        f"{int(round(firewood_vol)):,}".replace(',', '.'),
            
            # Số lượng và thể tích tổng hợp dạng số nguyên định dạng
            'total_quantity':         f"{int(total_qty):,}".replace(',', '.'),
            'total_volume':           f"{int(round(total_vol)):,}".replace(',', '.'),
            'quantity':               f"{int(total_qty):,}".replace(',', '.'),
            
            # Đọc số thành chữ tiếng Việt chuẩn xác
            'vietnamese_quantity':    number_to_vietnamese_words(total_qty),
            'vietnamese_volume':      number_to_vietnamese_words(total_vol),
            'vietnamese_firewood_quantity': number_to_vietnamese_words(firewood_qty),
            'vietnamese_firewood_volume':   number_to_vietnamese_words(firewood_vol),
            
            # Danh sách dòng bảng
            'table_rows':             bkls_rows,
        }
        return context

    def _prepare_ddnx_context(self):
        """[SKELETON] Đề nghị xuất (DDNX). TODO: bổ sung biến riêng."""
        _logger.info("[Renderer] _prepare_ddnx_context — tạm dùng context HDSG")
        return self._prepare_hop_dong_hsg_context()

    def _prepare_bbxm_context(self):
        """[SKELETON] Biên bản xác nhận mua (BBXM). TODO: bổ sung biến riêng."""
        _logger.info("[Renderer] _prepare_bbxm_context — tạm dùng context HDSG")
        return self._prepare_hop_dong_hsg_context()

    def _prepare_cnbk_context(self):
        """[SKELETON] Cam kết nghĩa vụ bảo kê (CNBK). TODO: bổ sung biến riêng."""
        _logger.info("[Renderer] _prepare_cnbk_context — tạm dùng context PAKT")
        return self._prepare_pakt_context()

    def _prepare_pnk_context(self):
        """[SKELETON] Phiếu nhập kho (PNK). TODO: bổ sung biến riêng."""
        _logger.info("[Renderer] _prepare_pnk_context — tạm dùng context HDSG")
        return self._prepare_hop_dong_hsg_context()

    def _prepare_bbbg_context(self):
        """[SKELETON] Biên bản bàn giao (BBBG). TODO: bổ sung biến riêng."""
        _logger.info("[Renderer] _prepare_bbbg_context — tạm dùng context HDSG")
        return self._prepare_hop_dong_hsg_context()

    def _prepare_gbn_context(self):
        """[SKELETON] Giấy biên nhận (GBN). TODO: bổ sung biến riêng."""
        _logger.info("[Renderer] _prepare_gbn_context — tạm dùng context HDSG")
        return self._prepare_hop_dong_hsg_context()
