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

from odoo import _, fields
from .address_utils import format_vietnamese_address

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
    if num is None or num is False:
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
            if hundreds == 0:
                res.append("không trăm")
            else:
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


def float_to_vietnamese_words(num):
    """
    Chuyển đổi một số float thành chữ tiếng Việt (lấy tối đa 2 chữ số thập phân).
    Ví dụ: 30.25 -> 'ba mươi phẩy hai mươi lăm'.
    """
    if num is None or num is False:
        return ""
    try:
        val = round(float(num), 2)
    except (ValueError, TypeError):
        return ""

    if val == 0.0:
        return "không"

    integer_part = int(val)
    decimal_part = int(round((val - integer_part) * 100))
    
    integer_words = number_to_vietnamese_words(integer_part)
    if integer_words:
        integer_words = integer_words[0].lower() + integer_words[1:]
        
    if decimal_part == 0:
        return integer_words[0].upper() + integer_words[1:] if integer_words else ""
    
    # Nếu phần thập phân chia hết cho 10 (ví dụ 10, 20, 30... tương ứng .1, .2, .3...)
    # ta rút gọn về 1 chữ số thập phân để đọc tự nhiên (ví dụ 33.4 đọc là 'ba mươi ba phẩy bốn')
    if decimal_part % 10 == 0:
        digit = decimal_part // 10
        units = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
        dec_words = [units[digit]]
    else:
        tens = decimal_part // 10
        ones = decimal_part % 10
        units = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
        
        dec_words = []
        if tens == 0:
            dec_words.append("không")
            dec_words.append(units[ones])
        elif tens == 1:
            dec_words.append("mười")
            if ones == 5:
                dec_words.append("lăm")
            elif ones > 0:
                dec_words.append(units[ones])
        else:
            dec_words.append(units[tens] + " mươi")
            if ones == 1:
                dec_words.append("mốt")
            elif ones == 5:
                dec_words.append("lăm")
            elif ones > 0:
                dec_words.append(units[ones])
                
    decimal_words = " ".join(dec_words)
    res = f"{integer_words} phẩy {decimal_words}"
    return res[0].upper() + res[1:] if res else ""


def format_volume_vietnamese(vol):
    """
    Định dạng thể tích/khối lượng hiển thị kiểu Việt Nam:
    - Nếu là số nguyên, không hiển thị phần lẻ (ví dụ: 150).
    - Nếu lẻ, hiển thị phần lẻ và bỏ các số 0 thừa ở cuối (ví dụ: 33,4 thay vì 33,40).
    """
    if vol is None or vol is False:
        return "0"
    try:
        val = float(vol)
    except (ValueError, TypeError):
        return "0"
        
    if abs(val - round(val)) < 0.001:
        return f"{int(round(val)):,}".replace(',', '.')
        
    s = f"{val:.3f}"
    s = s.rstrip('0').rstrip('.')
    return s.replace('.', ',')


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
        'cn_bkls':                  '_prepare_bkls_context',
        'chia_nho_bkls':            '_prepare_bkls_context',
        
        # Đơn đề nghị xác nhận
        'ddnx':                     '_prepare_ddnx_context',
        'don_de_nghi_xac_nhan':     '_prepare_ddnx_context',
        'xac_nhan_bkls':            '_prepare_ddnx_context',
        'xn_bkls':                  '_prepare_ddnx_context',
        
        # Biên bản xác minh
        'bbxm':                     '_prepare_bbxm_context',
        'bien_ban_xac_minh':        '_prepare_bbxm_context',
        'bien_ban_xac_minh_ngls':   '_prepare_bien_ban_xac_minh_ngls_context',
        
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

        if template_key in ('cn_bkls', 'chia_nho_bkls'):
            return self._render_cn_bkls(template_source)

        if template_key in ('pnk', 'phieu_nhap_kho'):
            return self._render_pnk(template_source)

        if template_key in ('bbbg', 'bien_ban_ban_giao'):
            return self._render_bbbg(template_source)


        context = self.get_context(template_key)
        context = self._add_context_helpers(context)
        doc = DocxTemplate(template_source)
        doc.render(context)
        
        # Tự động gộp ô dọc cho cột Đơn giá cố định trong hợp đồng HDSG
        if template_key in ('hdsg', 'hop_dong_hsg'):
            try:
                self._post_process_hdsg_cell_merge(doc)
            except Exception as e:
                _logger.error("Lỗi khi tự động gộp ô dọc cột Đơn giá HDSG: %s", e)

        output = io.BytesIO()
        doc.save(output)
        return output.getvalue()

    def _post_process_hdsg_cell_merge(self, doc):
        """
        Tự động quét qua tất cả các bảng trong hợp đồng, tìm cột chứa đơn giá cố định
        và thực hiện gộp ô dọc (Vertical Cell Merge) từ dòng dữ liệu đầu tiên đến dòng cuối cùng.
        """
        _logger.info("=== HDSG POST PROCESS: CELL MERGING START ===")
        _logger.info("Total tables in document: %d", len(doc.tables))
        
        from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.shared import Pt
        
        for t_idx, table in enumerate(doc.tables):
            _logger.info("Inspecting Table %d (Rows: %d)", t_idx, len(table.rows))
            target_col_idx = -1
            matching_rows = []
            
            for r_idx, row in enumerate(table.rows):
                for c_idx, cell in enumerate(row.cells):
                    txt = cell.text.strip()
                    if "Theo thỏa thuận, theo giá thị trường" in txt:
                        _logger.info("Match found in Table %d, Row %d, Col %d: '%s'", t_idx, r_idx, c_idx, txt[:40] + "...")
                        target_col_idx = c_idx
                        matching_rows.append(r_idx)
                        break
                        
            if target_col_idx != -1:
                _logger.info("Table %d target column is %d. Rows to merge: %s", t_idx, target_col_idx, matching_rows)
                if len(matching_rows) > 1:
                    start_row = matching_rows[0]
                    end_row = matching_rows[-1]
                    
                    _logger.info("Merging column %d from row %d to row %d in Table %d...", target_col_idx, start_row, end_row, t_idx)
                    start_cell = table.cell(start_row, target_col_idx)
                    end_cell = table.cell(end_row, target_col_idx)
                    
                    merged_text = "Theo thỏa thuận, theo giá thị trường tại từng thời điểm mua bán"
                    
                    # Thực hiện gộp ô dọc
                    start_cell.merge(end_cell)
                    
                    # Căn giữa và định dạng lại văn bản
                    start_cell.text = ""
                    p = start_cell.paragraphs[0]
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    run = p.add_run(merged_text)
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(11)
                    
                    # Căn giữa dọc
                    start_cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    _logger.info("Table %d column %d merged successfully!", t_idx, target_col_idx)
                else:
                    _logger.info("Only %d row matches found in Table %d. Merging skipped.", len(matching_rows), t_idx)
            else:
                _logger.info("No matching price cell found in Table %d.", t_idx)
                
        _logger.info("=== HDSG POST PROCESS: CELL MERGING END ===")

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
        idx = 1
        for line in self.dossier.line_ids:
            if line.wood_type == 'firewood' and (not line.volume_ster or line.volume_ster == 0.0):
                continue
            if line.wood_type == 'firewood':
                disp_vol = f"{line.volume_ster:.2f}".replace('.', ',')
                disp_qty = f"{line.volume_ster:.2f}".replace('.', ',')
                height_disp = ""
                diam_disp = ""
                unit_disp = "Ster"
            else:
                disp_vol = format_volume_vietnamese(line.volume)
                disp_qty = f"{int(line.quantity or 0):,}".replace(',', '.')
                height_disp = line.height_display or ""
                diam_disp = line.diameter_display or ""
                unit_disp = "m³"

            rows.append({
                'stt':           idx,
                'idx':           idx,
                'species':       line.species_id.name or "",
                'species_name':  line.species_id.name or "",
                'name_en':       line.name_en or "",
                'grade':         line.grade_id.name or "",
                'wood_type':     line.wood_type or "",
                'unit':          unit_disp,
                'quantity':      disp_qty,
                'volume':        disp_vol,
                'diameter':      diam_disp,
                'height':        height_disp,
                'price_unit':    f"{line.price_unit:,}".replace(',', '.'),
                'price_subtotal': f"{int(line.price_subtotal):,}".replace(',', '.'),
                'note':          line.note or "",
            })
            idx += 1
        return rows

    def _build_species_lines(self):
        """
        Xây dựng danh sách species_lines động phân biệt gỗ và củi.
        Dùng chung cho cả _prepare_bkls_context và _prepare_ddnx_context.
        """
        line_ids = self.dossier.line_ids
        species_lines = []
        for l in line_ids:
            if l.wood_type == 'firewood' and (not l.volume_ster or l.volume_ster == 0.0):
                continue
            if l.wood_type == 'firewood':
                label = "Củi"
                fmt_qty = f"{l.volume_ster:.2f}".replace('.', ',')
                fmt_vol = f"{l.volume_ster:.2f}".replace('.', ',')
                words_qty = number_to_vietnamese_words(int(round(l.volume_ster)))
                words_vol = float_to_vietnamese_words(l.volume_ster)
                unit_disp = "Ster"
                vietnamese_unit_disp = "Ster"
            else:
                label = "Gỗ"
                fmt_qty = f"{int(l.quantity):,}".replace(',', '.')
                fmt_vol = format_volume_vietnamese(l.volume)
                words_qty = number_to_vietnamese_words(l.quantity)
                words_vol = float_to_vietnamese_words(l.volume)
                unit_disp = "m³"
                vietnamese_unit_disp = "mét khối"
            
            # Viết chữ hoa chữ cái đầu tiên cho đẹp
            if words_qty:
                words_qty = words_qty[0].upper() + words_qty[1:]
            if words_vol:
                words_vol = words_vol[0].upper() + words_vol[1:]
                
            # Tạo dạng chữ của khối lượng bao gồm cả đơn vị m3 hay là ster
            if l.wood_type == 'firewood':
                vietnamese_volume_unit = f"{words_vol.lower() if words_vol else ''} Ster"
            else:
                vietnamese_volume_unit = f"{words_vol.lower() if words_vol else ''} mét khối"
            if vietnamese_volume_unit:
                vietnamese_volume_unit = vietnamese_volume_unit.strip()
                vietnamese_volume_unit = vietnamese_volume_unit[0].upper() + vietnamese_volume_unit[1:]
                
            species_lines.append({
                'wood_type': l.wood_type or 'wood',
                'species_label': label,
                'species_name': l.species_id.name or "",
                'quantity': fmt_qty,
                'volume': fmt_vol,
                'species_volume': fmt_vol,
                'vietnamese_quantity': words_qty,
                'vietnamese_quantity_lower': words_qty.lower() if words_qty else "",
                'vietnamese_volume': words_vol,
                'vietnamese_volume_unit': vietnamese_volume_unit,
                'unit': unit_disp,
                'vietnamese_unit': vietnamese_unit_disp,
            })
        return species_lines

    def _format_total_volume(self, wood_vol, firewood_ster):
        """
        Định dạng thể tích tổng cộng (Gỗ + Củi).
        - Nếu là số nguyên hoặc gần nguyên, hiển thị số nguyên (ví dụ: '150').
        - Nếu lẻ, hiển thị tối đa 2 chữ số thập phân (ví dụ: '150,25').
        """
        total_vol_all = (wood_vol or 0.0) + (firewood_ster or 0.0)
        if abs(total_vol_all - round(total_vol_all)) < 0.001:
            return f"{int(round(total_vol_all)):,}".replace(',', '.')
        else:
            total_volume_str = f"{total_vol_all:.2f}".replace('.', ',')
            if total_volume_str.endswith(',00'):
                total_volume_str = total_volume_str[:-3]
            return total_volume_str

    def _add_context_helpers(self, context):
        """Bổ sung các hàm helper dịch số thành chữ vào context."""
        if not isinstance(context, dict):
            return context
        context.update({
            'float_to_vietnamese_words': float_to_vietnamese_words,
            'number_to_vietnamese_words': number_to_vietnamese_words,
        })
        return context

    def _get_dossier_line_price_unit(self, species_id, wood_type):
        """Lấy đơn giá từ dòng hồ sơ gỗ khớp loài + phân loại."""
        if not species_id:
            return 0
        dossier_line = self.dossier.line_ids.filtered(
            lambda l: l.species_id == species_id and l.wood_type == wood_type
        )[:1]
        return dossier_line.price_unit if dossier_line else 0

    def _build_pnk_table_rows(self):
        """Bảng hàng hóa PNK theo toàn bộ hồ sơ (fallback khi không có phiếu)."""
        rows = []
        idx = 1
        for line in self.dossier.line_ids:
            vol_val = line.volume_ster if line.wood_type == 'firewood' else line.volume
            if not vol_val or vol_val == 0.0:
                continue
            disp_vol = f"{vol_val:.2f}".replace('.', ',') if line.wood_type == 'firewood' else format_volume_vietnamese(vol_val)
            rows.append({
                'idx': idx,
                'species_name': line.species_id.name or "",
                'volume': disp_vol,
                'price': f"{int(line.price_unit):,}".replace(',', '.'),
                'subtotal': f"{int(line.price_subtotal):,}".replace(',', '.'),
            })
            idx += 1
        return rows

    def _get_ticket_aggregates(self, ticket):
        """Gom nhóm khối lượng theo loài gỗ và loại gỗ từ phiếu nhập kho."""
        aggregates = {}

        if ticket.ticket_line_ids:
            _logger.info("[Ticket Aggregates] Ticket '%s' dung ticket_line_ids (%d dong)", ticket.name, len(ticket.ticket_line_ids))
            for line in ticket.ticket_line_ids:
                key = (line.species_id.id, line.wood_type)
                aggregates[key] = aggregates.get(key, 0.0) + (line.volume or 0.0)

        elif ticket.x_vehicle_ids:
            _logger.info("[Ticket Aggregates] Ticket '%s' dung x_vehicle_ids (%d xe)", ticket.name, len(ticket.x_vehicle_ids))
            for v_line in ticket.x_vehicle_ids:
                key = (v_line.species_id.id, v_line.wood_type)
                aggregates[key] = aggregates.get(key, 0.0) + (v_line.volume or 0.0)

        else:
            _logger.warning(
                "[Ticket Aggregates] Ticket '%s' khong co ticket_line_ids / x_vehicle_ids - fallback dossier lines",
                ticket.name,
            )
            d = self.dossier
            dossier_total = sum(d.line_ids.mapped('volume')) or 1.0
            ticket_vol = ticket.total_volume or 0.0
            ratio = ticket_vol / dossier_total if dossier_total else 1.0
            for line in d.line_ids:
                key = (line.species_id.id, line.wood_type)
                aggregates[key] = aggregates.get(key, 0.0) + round(line.volume * ratio, 3)
        return aggregates

    def _build_pnk_table_rows_from_ticket(self, ticket):
        """Bảng hàng hóa PNK theo chi tiết một phiếu nhập kho (theo ngày/chuyến)."""
        aggregates = self._get_ticket_aggregates(ticket)
        rows = []
        idx = 1
        for (species_id, wood_type), volume in sorted(aggregates.items()):
            if not volume or volume == 0.0:
                continue
            species = self.dossier.env['dl.wood.species'].browse(species_id)
            price_unit = self._get_dossier_line_price_unit(species, wood_type)
            subtotal = round(volume * price_unit, 2)
            if wood_type == 'firewood':
                disp_vol = f"{volume:.2f}".replace('.', ',')
            else:
                disp_vol = format_volume_vietnamese(volume)
            rows.append({
                'idx': idx,
                'species_name': species.name or "",
                'volume': disp_vol,
                'price': f"{int(price_unit):,}".replace(',', '.'),
                'subtotal': f"{int(subtotal):,}".replace(',', '.'),
                '_subtotal_raw': subtotal,
            })
            idx += 1

        _logger.info("[PNK] Ticket '%s' -> %d dong hang hoa", ticket.name, len(rows))
        return rows

    def _build_bbbg_table_rows_from_ticket(self, ticket):
        """Bảng hàng hóa BBBG theo chi tiết một phiếu nhập kho."""
        aggregates = self._get_ticket_aggregates(ticket)
        rows = []
        idx = 1
        for (species_id, wood_type), volume in sorted(aggregates.items()):
            if not volume or volume == 0.0:
                continue
            species = self.dossier.env['dl.wood.species'].browse(species_id)
            x_unit = 'm³' if wood_type == 'wood' else 'Ster'
            if wood_type == 'firewood':
                disp_vol = f"{volume:.2f}".replace('.', ',')
            else:
                disp_vol = format_volume_vietnamese(volume)
            rows.append({
                'idx': idx,
                'species_name': species.name or "",
                'x_unit': x_unit,
                'volume': disp_vol,
            })
            idx += 1

        _logger.info("[BBBG] Ticket '%s' -> %d dong hang hoa", ticket.name, len(rows))
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
            # Thông tin thanh toán (Ngân hàng)
            'owner_bank_account_number': p.x_bank_account_number or "",
            'owner_bank_account_holder': p.x_bank_account_holder or "",
            'owner_bank_name':           p.x_bank_name or "",
            # Các biến thanh toán mới của chủ rừng theo template HD_HSG mới
            'bank_name':                 p.x_bank_name or "",
            'forest_owner_bank_name':    p.x_bank_name or "",
            'forest_owner_acc_hoder':    p.x_bank_account_holder or "",
            'forest_owner_acc_holder':   p.x_bank_account_holder or "",
            'forest_owner_bank_acc':     p.x_bank_account_number or "",
            'forest_owner_bank_account': p.x_bank_account_number or "",
            # Dự phòng các biến viết tắt khác để dễ dùng trong template Word
            'owner_bank_acc':            p.x_bank_account_number or "",
            'owner_bank_holder':         p.x_bank_account_holder or "",
            'owner_bank':                p.x_bank_name or "",
            'owner_acc':                 p.x_bank_account_number or "",
        }

    def _get_company_info(self):
        """Trích xuất thông tin công ty (bên mua) thành dict."""
        c = self.dossier.company_id
        d = self.dossier
        rep = d.x_company_representative or c.x_representative or ""
        pos = d.x_company_position or getattr(c, 'x_representative_position', '') or "Giám đốc"
        
        # Lấy đầy đủ thông tin địa chỉ thôn, xã, huyện, tỉnh của công ty
        company_address = format_vietnamese_address(
            street=c.street,
            street2=c.street2,
            city=c.city,
            state_name=c.state_id.name
        )

        return {
            'company_name':                    c.name or "",
            'company_address':                 company_address,
            'company_tax_number':              c.vat or "",
            'company_representative':          rep,
            'company_ representative':         rep,   # dự phòng lỗi gõ phím trong template cũ
            'company_representative_position': pos,
            'representative_position':         pos,
            'representative':                  rep,
            'position':                        pos,
            'companyName':                     c.name or "",
            'inventory_clerk':                 getattr(c, 'x_inventory_inspector', '') or "",
            'inventory_clerk_position':        getattr(c, 'x_inventory_inspector_position', '') or "",
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

        # Tính số ngày vận chuyển
        delivery_days = 0
        if d.x_delivery_start_date and d.x_delivery_end_date:
            delivery_days = (d.x_delivery_end_date - d.x_delivery_start_date).days + 1

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
            
            # Các biến bổ sung theo yêu cầu Hợp đồng và Phụ lục mới
            'contract_number':  d.x_contract_number or "",
            'vietnamese_x_contract_date': date_to_vietnamese_text(d.x_contract_date),
            'forest_owner_address': d.partner_address or "",
            'vietnamese_x_delivery_start_date': date_to_vietnamese_text(d.x_delivery_start_date),
            'vietnamese_x_delivery_end_date':   date_to_vietnamese_text(d.x_delivery_end_date),
            'delivery_count_day': delivery_days,
            'x_addendum_num':   d.x_addendum_num or "",
            'species_name':     main_species,
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
        c_rep = d.x_company_representative or d.company_id.x_representative or ""
        c_pos = d.x_company_position or getattr(d.company_id, 'x_representative_position', '') or "Giám đốc"

        loc = d.exploitation_location_id
        if loc:
            forest_addr = format_vietnamese_address(
                street=loc.street,
                city=loc.city,
                state_name=loc.state_id.name
            ) or loc.name or ""
        else:
            forest_addr = d.partner_address or ""

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
            'forestAddr':             forest_addr,
            'typeMining':             mining_method_map.get(d.x_mining_method, ""),
            'projectedMiningOutput':  ", ".join([
                f"{l.species_id.name} " + (
                    f"{l.volume_ster:.2f}".replace('.', ',') + " Ster"
                    if l.wood_type == 'firewood'
                    else f"{int(round(l.volume)):,}".replace(',', '.') + " m³"
                )
                for l in d.line_ids
            ]) if d.line_ids else "0 m³",
            # Thời gian khai thác
            'miningFromDate':         date_to_vietnamese_text(d.x_start_date),
            'miningFromdate':         date_to_vietnamese_text(d.x_start_date),  # dự phòng
            'miningToDate':           date_to_vietnamese_text(d.x_end_date),
            # Đại diện công ty
            'representative':         c_rep,
            'position':               c_pos,
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
            
        delivery_days = 0
        if d.x_delivery_start_date and d.x_delivery_end_date:
            delivery_days = (d.x_delivery_end_date - d.x_delivery_start_date).days + 1
            
        # 2. Phân nhóm lâm sản (Gỗ vs Củi)
        line_ids = d.line_ids
        wood_lines = line_ids.filtered(lambda l: l.wood_type == 'wood')
        firewood_lines = line_ids.filtered(lambda l: l.wood_type == 'firewood' and l.volume_ster > 0)
        
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
        
        # Tính cực trị đường kính (chỉ tính cho gỗ)
        dia_min = min(wood_lines.mapped('diameter_min')) if wood_lines and any(wood_lines.mapped('diameter_min')) else 0
        dia_max = max(wood_lines.mapped('diameter_max')) if wood_lines and any(wood_lines.mapped('diameter_max')) else 0
        
        # Tính toán sản lượng
        total_vol = sum(wood_lines.mapped('volume'))  # Chỉ tính gỗ (m³)
        total_qty = sum(line_ids.mapped('quantity'))
        
        wood_vol = sum(wood_lines.mapped('volume'))
        wood_qty = sum(wood_lines.mapped('quantity'))
        
        # Củi tính theo Ster
        firewood_ster = sum(firewood_lines.mapped('volume_ster'))
        firewood_qty = sum(firewood_lines.mapped('quantity'))  # giữ tương thích cũ
        firewood_vol = firewood_ster  # alias dùng dưới
        
        # 3. Xây dựng danh sách hàng bảng chi tiết
        bkls_rows = []
        idx = 1
        for line in line_ids:
            if line.wood_type == 'firewood' and (not line.volume_ster or line.volume_ster == 0.0):
                continue
            val = line.species_id.x_species_group or 'common'
            group_label = {
                'common': 'Thông thường',
                'precious': 'Danh mục loài nguy cấp, quý, hiếm',
                'cites': 'Phụ lục CITES'
            }.get(val, 'Thông thường')

            if line.wood_type == 'firewood':
                # Củi: hiển thị volume_ster và đơn vị Ster
                disp_vol = f"{line.volume_ster:.2f}".replace('.', ',')
                disp_qty = f"{line.volume_ster:.2f}".replace('.', ',')
                height_disp = ""
                diam_disp = ""
            else:
                disp_vol = format_volume_vietnamese(line.volume)
                disp_qty = f"{int(line.quantity or 0):,}".replace(',', '.')
                height_disp = line.height_display or ""
                diam_disp = line.diameter_display or ""

            bkls_rows.append({
                'idx':           idx,
                'stt':           idx,
                'species_name':  line.species_id.name or "",
                'name_sci':      line.name_sci or "",
                'name_en':       line.name_en or "",
                'type':          group_label,
                'height':        height_disp,
                'diameter':      diam_disp,
                'volume':        disp_vol,
                'quantity':      disp_qty,
                'unit':          'm³' if line.wood_type == 'wood' else 'Ster',
                'wood_type':     line.wood_type or 'wood',
            })
            idx += 1
            
        # Mã số và ngày lập bảng kê lâm sản
        bkls_date = d.x_bkls_date or d.x_contract_date or d.x_end_date or fields.Date.today()
        vietnamese_bkls_date = date_to_vietnamese_text(bkls_date)
        forest_owner_city = p.city or p.state_id.name or ""
        
        species_lines = self._build_species_lines()
        
        # Địa chỉ khai thác đầy đủ
        exploitation_address = d._get_exploitation_address()
            
        # Fallback variables cho context cha nếu người dùng viết không có tiền tố line.
        fallback_vietnamese_volume_unit = species_lines[0]['vietnamese_volume_unit'] if species_lines else ""
        fallback_vietnamese_unit = species_lines[0]['vietnamese_unit'] if species_lines else ""

        total_volume_str = self._format_total_volume(wood_vol, firewood_ster)

        has_firewood = firewood_ster > 0
        disp_firewood_ster = f"{firewood_ster:.2f}".replace('.', ',') if has_firewood else ""
        vietnamese_firewood_qty = number_to_vietnamese_words(int(round(firewood_ster))) if has_firewood else ""

        context = {
            # Bảng kê lâm sản
            'bkls_number':            d.x_bkls_number or "",
            'bkls_code':              d.x_bkls_number or "",
            'vietnamese_bkls_date':   vietnamese_bkls_date,
            'vietnamses_bkls_date':   vietnamese_bkls_date, # Dự phòng lỗi chính tả trong template
            'forest_owner_city':      forest_owner_city,

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
            'exploitation_address':   exploitation_address,
            'exploitation_count_day': count_days,
            'delivery_count_day':     delivery_days,
            'vietnamese_exploitation_from_date': date_to_vietnamese_text(d.x_start_date),
            'vietnamese_exploitation_to_date':   date_to_vietnamese_text(d.x_end_date),
            'vietnamese_x_delivery_start_date': date_to_vietnamese_text(d.x_delivery_start_date),
            'vietnamese_x_delivery_end_date':   date_to_vietnamese_text(d.x_delivery_end_date),
            
            # Đường kính cực trị (hỗ trợ cả biến đã sửa và biến lỗi chính tả cũ)
            'diameter_min':           dia_min,
            'diameter_max':           dia_max,
            'diametter_max':          dia_max, # dự phòng lỗi chính tả cũ
            
            # Nhóm loài & Loại lâm sản
            'species_name':           main_species,
            'species_type':           main_type,
            'species_volume':         format_volume_vietnamese(wood_vol),
            # Củi xuất theo Ster
            'firewood_ster':          disp_firewood_ster,   # biến mới rõ ràng
            'firewood_quantity':      disp_firewood_ster,   # tương thích template cũ
            'firewood_volume':        disp_firewood_ster,   # tương thích template cũ
            
            # Số lượng và thể tích tổng hợp dạng số nguyên định dạng (chỉ gỗ)
            'total_quantity':         f"{int(wood_qty):,}".replace(',', '.'),
            'total_volume':           total_volume_str,
            'quantity':               f"{int(wood_qty):,}".replace(',', '.'),
            
            # Đọc số thành chữ tiếng Việt chuẩn xác
            'vietnamese_quantity':    number_to_vietnamese_words(wood_qty),
            'vietnamese_volume':      float_to_vietnamese_words(wood_vol),
            'vietnamese_firewood_quantity': vietnamese_firewood_qty,
            'vietnamese_firewood_volume':   vietnamese_firewood_qty,
            'vietnamese_firewood_ster':     vietnamese_firewood_qty,
            
            # Danh sách dòng bảng
            'table_rows':             bkls_rows,
            'species_lines':          species_lines,

            # Fallback variables
            'vietnamese_volume_unit':   fallback_vietnamese_volume_unit,
            'vietnamese_unit':          fallback_vietnamese_unit,
        }
        return context

    def _prepare_ddnx_context(self):
        """
        Chuẩn bị dữ liệu cho Đơn đề nghị xác nhận Bảng kê lâm sản (xac_nhan_bkls / ddnx).
        
        Quy tắc nghiệp vụ:
          - Ngày lập đơn/ngày xin xác nhận = Ngày cuối cùng khai thác (x_end_date) + 1 ngày.
        """
        self.dossier.ensure_one()
        d = self.dossier
        p = d.partner_id
        
        # 1. Lấy ngày xin xác nhận / Kiểm lâm xác nhận
        proposal_date = d.x_verify_date or d.x_contract_date or d.x_end_date or fields.Date.today()
        vietnamese_proposal_date = date_to_vietnamese_text(proposal_date)
        
        # 2. Lấy thông tin công ty và chủ rừng
        company_info = self._get_company_info()
        owner_info = self._get_owner_info()
        
        # 3. Phân nhóm lâm sản (Gỗ vs Củi) để tính toán
        line_ids = d.line_ids
        wood_lines = line_ids.filtered(lambda l: l.wood_type == 'wood')
        firewood_lines = line_ids.filtered(lambda l: l.wood_type == 'firewood' and l.volume_ster > 0)
        
        species_lines = self._build_species_lines()
        
        main_species = ", ".join(list(set(line_ids.filtered(lambda l: l.species_id).mapped('species_id.name')))) if line_ids else ""
        
        # Tính toán sản lượng
        total_wood_vol = sum(wood_lines.mapped('volume'))
        total_wood_qty = sum(wood_lines.mapped('quantity'))
        total_firewood_ster = sum(firewood_lines.mapped('volume_ster'))
        
        # Lấy địa danh (Xã/Phường) của địa bàn khai thác
        commune_name = d.exploitation_location_id.city or p.city or ""
        
        # Địa chỉ khai thác đầy đủ
        exploitation_address = d._get_exploitation_address()
        
        # Lấy Hạt kiểm lâm quản lý (nếu có trường x_ranger_agency hoặc mặc định bỏ trống)
        ranger_agency = getattr(d, 'x_ranger_agency', '') or ""
        
        total_vol_str = self._format_total_volume(total_wood_vol, total_firewood_ster)

        # Fallback variables cho context cha nếu người dùng viết không có tiền tố line.
        fallback_vietnamese_volume_unit = species_lines[0]['vietnamese_volume_unit'] if species_lines else ""
        fallback_vietnamese_unit = species_lines[0]['vietnamese_unit'] if species_lines else ""

        has_firewood = total_firewood_ster > 0
        disp_firewood_ster = f"{total_firewood_ster:.2f}".replace('.', ',') if has_firewood else ""
        vietnamese_firewood_ster = number_to_vietnamese_words(int(round(total_firewood_ster))) if has_firewood else ""
        
        context = {
            # Kính gửi
            'ranger_agency':            ranger_agency,
            'district_ranger_office':   ranger_agency,
            
            # Thông tin chủ rừng (Bên bán)
            'forest_owner_name':        p.name or "",
            'forest_owner_cccd':        p.x_cccd or "",
            'forest_owner_address':     d.partner_address or "",
            'forest_owner_phone':       p.phone or "",
            'forest_owner_email':       p.email or "",
            
            # Thông tin lâm sản
            'species_name':             main_species,
            
            # Định dạng số lượng và khối lượng (tổng cả gỗ và củi)
            'quantity':                 f"{int(total_wood_qty):,}".replace(',', '.'),
            'volume':                   total_vol_str,
            'total_quantity':           f"{int(total_wood_qty):,}".replace(',', '.'),
            'total_volume':             total_vol_str,
            'firewood_ster':            disp_firewood_ster,
            'firewood_quantity':        disp_firewood_ster,
            'firewood_volume':          disp_firewood_ster,
            
            # Đọc số thành chữ tiếng Việt chuẩn xác
            'vietnamese_quantity':      number_to_vietnamese_words(total_wood_qty),
            'vietnamese_volume':        float_to_vietnamese_words(total_wood_vol),
            'vietnamese_firewood_ster':  vietnamese_firewood_ster,
            'vietnamese_firewood_quantity': vietnamese_firewood_ster,
            'vietnamese_firewood_volume':   vietnamese_firewood_ster,
            
            # Địa chỉ khai thác
            'exploitation_address':     exploitation_address,
            
            # Thông tin bảng kê
            'bkls_number':              d.x_bkls_number or d.name or "",
            'bkls_code':                d.x_bkls_number or d.name or "",
            'proposal_date':            proposal_date.strftime('%d/%m/%Y') if proposal_date else "",
            'vietnamese_bkls_date':     vietnamese_proposal_date,
            'vietnamses_bkls_date':     vietnamese_proposal_date, # Dự phòng lỗi chính tả trong template
            'vietnamese_proposal_date': vietnamese_proposal_date,
            
            # Địa danh & Ký tên
            'forest_owner_city':        commune_name,
            'commune_name':             commune_name,
            'location_commune':         commune_name,
            'species_lines':            species_lines,
            
            # Fallback variables
            'vietnamese_volume_unit':   fallback_vietnamese_volume_unit,
            'vietnamese_unit':          fallback_vietnamese_unit,
        }
        return context

    def _prepare_bbxm_context(self):
        """[SKELETON] Biên bản xác nhận mua (BBXM). TODO: bổ sung biến riêng."""
        _logger.info("[Renderer] _prepare_bbxm_context — tạm dùng context HDSG")
        return self._prepare_hop_dong_hsg_context()

    def _prepare_cnbk_context(self):
        """[SKELETON] Cam kết nghĩa vụ bảo kê (CNBK). TODO: bổ sung biến riêng."""
        _logger.info("[Renderer] _prepare_cnbk_context — tạm dùng context PAKT")
        return self._prepare_pakt_context()

    def _prepare_pnk_context_for_ticket(self, ticket):
        """
        Context PNK cho một phiếu nhập kho (dl.wood.dossier.transport.ticket).
        Mỗi phiếu = một ngày nhập kho với khối lượng các xe trong ngày đó.
        """
        self.dossier.ensure_one()
        d = self.dossier
        p = d.partner_id

        table_rows = self._build_pnk_table_rows_from_ticket(ticket)
        total_vol = ticket.total_volume or sum(
            ticket.ticket_line_ids.mapped('volume')
        ) or sum(ticket.x_vehicle_ids.mapped('volume'))
        total_amt = sum(r.pop('_subtotal_raw', 0) for r in table_rows)
        pnk_date = ticket.x_date or d.x_contract_date or fields.Date.today()

        is_firewood = False
        if ticket.ticket_line_ids:
            is_firewood = any(l.wood_type == 'firewood' for l in ticket.ticket_line_ids)
        elif ticket.x_vehicle_ids:
            is_firewood = any(v.wood_type == 'firewood' for v in ticket.x_vehicle_ids)

        if is_firewood:
            disp_total_vol = f"{total_vol:.2f}".replace('.', ',')
        else:
            disp_total_vol = format_volume_vietnamese(total_vol)

        return {
            **self._get_company_info(),
            'forest_owner_name': p.name or "",
            'forest_owner_cccd': p.x_cccd or "",
            'forest_owner_cccd_date': date_to_vietnamese_text(p.x_cccd_date),
            'vietnamese_ticket_date': date_to_vietnamese_text(pnk_date),
            'table_rows': table_rows,
            'total_volme': disp_total_vol,
            'total_volume': disp_total_vol,
            'total': f"{int(total_amt):,}".replace(',', '.'),
            'vietnamese_total': number_to_vietnamese_words(total_amt),
            'contract_number': d.x_contract_number or "",
            'vietnamese_contract_date': date_to_vietnamese_text(d.x_contract_date),
            'pnk_number': ticket.name or d.name or "",
            'ticket_name': ticket.name or "",
            'vehicle_count': ticket.vehicle_count or 0,
            'vehicle_info': ticket.x_vehicle_info or "",
        }

    def _prepare_pnk_context(self):
        """
        Context PNK tổng hợp cả hồ sơ (dùng khi không có ticket_ids).
        """
        self.dossier.ensure_one()
        d = self.dossier
        p = d.partner_id

        pnk_date = d.x_contract_date or d.x_bkls_date or fields.Date.today()
        total_amt = d.total_amount or 0.0

        has_wood = any(l.wood_type == 'wood' for l in d.line_ids)
        if has_wood:
            disp_total_vol = format_volume_vietnamese(d.initial_wood_qty)
        else:
            disp_total_vol = f"{d.initial_firewood_qty:.2f}".replace('.', ',') if d.initial_firewood_qty else ""

        context = {
            **self._get_company_info(),
            'forest_owner_name': p.name or "",
            'forest_owner_cccd': p.x_cccd or "",
            'forest_owner_cccd_date': date_to_vietnamese_text(p.x_cccd_date),
            'vietnamese_ticket_date': date_to_vietnamese_text(pnk_date),
            'table_rows': self._build_pnk_table_rows(),
            'total_volme': disp_total_vol,
            'total_volume': disp_total_vol,
            'total': f"{int(total_amt):,}".replace(',', '.'),
            'vietnamese_total': number_to_vietnamese_words(total_amt),
            'contract_number': d.x_contract_number or "",
            'vietnamese_contract_date': date_to_vietnamese_text(d.x_contract_date),
            'pnk_number': d.name or "",
        }
        _logger.info("[Renderer] _prepare_pnk_context: %s", context)
        return context

    def _render_pnk(self, template_source):
        """
        Render Phiếu nhập kho: một file docx cho mỗi ticket_ids, ghép bằng docxcompose.
        """
        from odoo.exceptions import UserError

        if not DocxTemplate:
            raise ImportError("Thư viện 'docxtpl' chưa được cài đặt trên máy chủ.")

        d = self.dossier
        tickets = d.ticket_ids.sorted(
            key=lambda t: (t.x_date or fields.Date.today(), t.name or '')
        )
        if not tickets:
            _logger.warning(
                "[Renderer] Hồ sơ %s không có phiếu nhập kho — xuất PNK tổng hợp.",
                d.name,
            )
            context = self._prepare_pnk_context()
            context = self._add_context_helpers(context)
            doc = DocxTemplate(template_source)
            doc.render(context)
            output = io.BytesIO()
            doc.save(output)
            return output.getvalue()

        rendered_docs_bytes = []
        for ticket in tickets:
            context = self._prepare_pnk_context_for_ticket(ticket)
            context = self._add_context_helpers(context)
            doc = DocxTemplate(template_source)
            doc.render(context)
            ticket_io = io.BytesIO()
            doc.save(ticket_io)
            rendered_docs_bytes.append(ticket_io.getvalue())
            _logger.info(
                "[Renderer] PNK ticket '%s' date=%s vol=%s rows=%s",
                ticket.name,
                ticket.x_date,
                ticket.total_volume,
                len(context.get('table_rows', [])),
            )

        dossier_vol = sum(d.line_ids.mapped('volume'))
        tickets_vol = sum(tickets.mapped('total_volume'))
        if dossier_vol and abs(tickets_vol - dossier_vol) > 0.5:
            _logger.warning(
                "[Renderer] PNK tổng phiếu (%.1f m³) ≠ tổng hồ sơ (%.1f m³) — %s",
                tickets_vol, dossier_vol, d.name,
            )

        return self._merge_docx_files(rendered_docs_bytes)

    def _prepare_bbbg_context(self):
        """
        Context BBBG tổng hợp cả hồ sơ (dùng khi không có ticket_ids).
        """
        self.dossier.ensure_one()
        d = self.dossier
        p = d.partner_id
        
        table_rows = []
        idx = 1
        for line in d.line_ids:
            vol_val = line.volume_ster if line.wood_type == 'firewood' else line.volume
            if not vol_val or vol_val == 0.0:
                continue
            x_unit = 'm³' if line.wood_type == 'wood' else 'Ster'
            disp_vol = f"{vol_val:.2f}".replace('.', ',') if line.wood_type == 'firewood' else format_volume_vietnamese(vol_val)
            table_rows.append({
                'idx': idx,
                'species_name': line.species_id.name or "",
                'x_unit': x_unit,
                'volume': disp_vol,
            })
            idx += 1

        ticket_x_date = d.x_contract_date or d.x_bkls_date or fields.Date.today()
        
        has_wood = any(l.wood_type == 'wood' for l in d.line_ids)
        if has_wood:
            disp_total_vol = format_volume_vietnamese(d.initial_wood_qty)
        else:
            disp_total_vol = f"{d.initial_firewood_qty:.2f}".replace('.', ',') if d.initial_firewood_qty else ""

        context = {
            **self._get_company_info(),
            'forest_owner_name': p.name or "",
            'forest_owner_address': d.partner_address or "",
            'forest_owner_cccd': p.x_cccd or "",
            'forest_owner_cccd_date': self._format_date(p.x_cccd_date),
            'forest_owner_cccd_place': p.x_cccd_place or "",
            'contract_date': self._format_date(d.x_contract_date),
            'ticket_x_date': date_to_vietnamese_text(ticket_x_date),
            'table_rows': table_rows,
            'total_volume': disp_total_vol,
        }
        _logger.info("[Renderer] _prepare_bbbg_context: %s", context)
        return context

    def _prepare_bbbg_context_for_ticket(self, ticket):
        """
        Context BBBG cho một phiếu nhập kho.
        """
        self.dossier.ensure_one()
        d = self.dossier
        p = d.partner_id

        table_rows = self._build_bbbg_table_rows_from_ticket(ticket)
        total_vol = ticket.total_volume or sum(
            ticket.ticket_line_ids.mapped('volume')
        ) or sum(ticket.x_vehicle_ids.mapped('volume'))
        bbbg_date = ticket.x_date or d.x_contract_date or fields.Date.today()

        is_firewood = False
        if ticket.ticket_line_ids:
            is_firewood = any(l.wood_type == 'firewood' for l in ticket.ticket_line_ids)
        elif ticket.x_vehicle_ids:
            is_firewood = any(v.wood_type == 'firewood' for v in ticket.x_vehicle_ids)

        if is_firewood:
            disp_total_vol = f"{total_vol:.2f}".replace('.', ',')
        else:
            disp_total_vol = format_volume_vietnamese(total_vol)

        return {
            **self._get_company_info(),
            'forest_owner_name': p.name or "",
            'forest_owner_address': d.partner_address or "",
            'forest_owner_cccd': p.x_cccd or "",
            'forest_owner_cccd_date': self._format_date(p.x_cccd_date),
            'forest_owner_cccd_place': p.x_cccd_place or "",
            'contract_date': self._format_date(d.x_contract_date),
            'ticket_x_date': date_to_vietnamese_text(bbbg_date),
            'table_rows': table_rows,
            'total_volume': disp_total_vol,
        }

    def _render_bbbg(self, template_source):
        """
        Render Biên bản bàn giao: mỗi phiếu nhập kho (ticket) là 1 biên bản,
        sau đó gộp lại bằng docxcompose thành 1 file tổng.
        """
        if not DocxTemplate:
            raise ImportError("Thư viện 'docxtpl' chưa được cài đặt trên máy chủ.")

        d = self.dossier
        tickets = d.ticket_ids.sorted(
            key=lambda t: (t.x_date or fields.Date.today(), t.name or '')
        )
        if not tickets:
            _logger.warning(
                "[Renderer] Hồ sơ %s không có phiếu nhập kho — xuất BBBG tổng hợp.",
                d.name,
            )
            context = self._prepare_bbbg_context()
            context = self._add_context_helpers(context)
            doc = DocxTemplate(template_source)
            doc.render(context)
            output = io.BytesIO()
            doc.save(output)
            return output.getvalue()

        rendered_docs_bytes = []
        for ticket in tickets:
            context = self._prepare_bbbg_context_for_ticket(ticket)
            context = self._add_context_helpers(context)
            doc = DocxTemplate(template_source)
            doc.render(context)
            ticket_io = io.BytesIO()
            doc.save(ticket_io)
            rendered_docs_bytes.append(ticket_io.getvalue())
            _logger.info(
                "[Renderer] BBBG ticket '%s' date=%s vol=%s rows=%s",
                ticket.name,
                ticket.x_date,
                ticket.total_volume,
                len(context.get('table_rows', [])),
            )

        return self._merge_docx_files(rendered_docs_bytes)


    def _prepare_gbn_context(self):
        """[SKELETON] Giấy biên nhận (GBN). TODO: bổ sung biến riêng."""
        _logger.info("[Renderer] _prepare_gbn_context — tạm dùng context HDSG")
        return self._prepare_hop_dong_hsg_context()

    def _prepare_bien_ban_xac_minh_ngls_context(self):
        """
        Chuẩn bị dữ liệu cho Biên bản xác minh nguồn gốc lâm sản (bien_ban_xac_minh_ngls).
        """
        self.dossier.ensure_one()
        d = self.dossier
        p = d.partner_id

        # 1. Tên loài cây gỗ/lâm sản
        species_name = ", ".join(
            list(set(d.line_ids.filtered(lambda l: l.species_id).mapped('species_id.name')))
        ) if d.line_ids else ""

        # 2. Khối lượng và chữ số
        total_vol = d.initial_qty or 0.0
        total_volume_str = format_volume_vietnamese(total_vol)
        vietnamese_total_volume = float_to_vietnamese_words(total_vol)

        # 3. Diện tích ha
        x_area = f"{d.x_area:.2f}".replace('.', ',') if d.x_area else "0"
        
        # 4. Địa chỉ rừng và địa điểm xác minh
        forest_addr = d._get_exploitation_address()
        vietnamese_forest_address = forest_addr
        
        # 5. Các mốc thời gian dạng chữ Tiếng Việt thông minh
        x_bkls_date_str = date_to_vietnamese_text(d.x_bkls_date)
        x_verify_date_str = date_to_vietnamese_text(d.x_verify_date)
        
        # Để tránh lặp từ "ngày" nếu trong template đã ghi sẵn: "từ ngày {{vietnamese_x_start_date}}"
        vietnamese_x_start_date = ""
        if d.x_start_date:
            vietnamese_x_start_date = f"{d.x_start_date.day:02d} tháng {d.x_start_date.month:02d} năm {d.x_start_date.year}"
            
        # Không có chữ "ngày" trong template trước {{vietnamese_x_end_date}}, nên phải có chữ "ngày" ở đầu
        vietnamese_x_end_date = ""
        if d.x_end_date:
            vietnamese_x_end_date = f"ngày {d.x_end_date.day:02d} tháng {d.x_end_date.month:02d} năm {d.x_end_date.year}"

        context = {
            'x_bkls_date':               x_bkls_date_str,
            'forest_owner_name':         p.name or "",
            'x_verify_date':             x_verify_date_str,
            'vietnamese_forest_address':  vietnamese_forest_address,
            'species_name':              species_name,
            'x_area':                    x_area,
            'forest_address':            forest_addr,
            'total_volume':              total_volume_str,
            'vietnamese_total_volume':   vietnamese_total_volume,
            'forest_owner_cccd':         p.x_cccd or "",
            'vietnamese_x_start_date':   vietnamese_x_start_date,
            'vietnamese_x_end_date':     vietnamese_x_end_date,
        }
        
        _logger.info("[Renderer] bien_ban_xac_minh_ngls context: %s", context)
        return context

    def _prepare_cn_bkls_context_for_vehicle(self, ticket, v_name, capacity, v_target_vol, v_lines, ticket_date):
        """
        Chuẩn bị context Bảng kê lâm sản chi tiết cho từng xe vận chuyển.
        Tương tự _prepare_bkls_context nhưng các số lượng, khối lượng, table_rows
        được tính toán riêng cho xe này.
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
            
        delivery_days = 0
        if d.x_delivery_start_date and d.x_delivery_end_date:
            delivery_days = (d.x_delivery_end_date - d.x_delivery_start_date).days + 1
            
        vietnamese_ticket_date = date_to_vietnamese_text(ticket_date)
        forest_owner_city = p.city or p.state_id.name or ""
        
        # Cực trị đường kính (chỉ tính cho gỗ)
        wood_lines = d.line_ids.filtered(lambda l: l.wood_type == 'wood')
        dia_min = min(wood_lines.mapped('diameter_min')) if wood_lines and any(wood_lines.mapped('diameter_min')) else 0
        dia_max = max(wood_lines.mapped('diameter_max')) if wood_lines and any(wood_lines.mapped('diameter_max')) else 0
        
        # Xây dựng table_rows và tính tổng sản lượng
        table_rows = []
        species_lines = []
        total_qty = 0
        total_vol = 0.0
        wood_vol = 0.0
        wood_qty = 0
        firewood_vol = 0.0
        firewood_qty = 0
        
        idx = 1
        for line in v_lines:
            species = line['species_id']
            wood_type = line['wood_type']
            vol_val = line['volume']
            
            if not vol_val or vol_val == 0.0:
                continue
            
            # Tìm dossier line để lấy quy cách (đường kính, chiều cao, tên khoa học, v.v.)
            dossier_line = d.line_ids.filtered(lambda l: l.species_id == species and l.wood_type == wood_type)[:1]
            
            if wood_type == 'firewood':
                # Củi: dùng volume_ster làm căn cứ hiển thị
                ster_val = dossier_line.volume_ster if dossier_line else vol_val
                if not ster_val or ster_val == 0.0:
                    continue
                computed_qty = int(round(ster_val)) if ster_val > 0 else 1
                height_display = ""
                name_sci = dossier_line.name_sci if dossier_line else ""
                name_en = dossier_line.name_en if dossier_line else ""
                firewood_vol += ster_val
                firewood_qty += computed_qty
            else:
                # Gỗ: tính số lượng theo tỷ lệ khối lượng
                avg_vol_per_unit = 0.1
                height_display = ""
                name_sci = ""
                name_en = ""
                if dossier_line:
                    d_vol = dossier_line.volume
                    d_qty = dossier_line.quantity
                    if d_qty > 0:
                        avg_vol_per_unit = d_vol / d_qty
                    height_display = dossier_line.height_display or ""
                    name_sci = dossier_line.name_sci or ""
                    name_en = dossier_line.name_en or ""
                computed_qty = max(1, int(round(vol_val / avg_vol_per_unit))) if avg_vol_per_unit > 0 else 1
                wood_vol += vol_val
                wood_qty += computed_qty
            
            total_qty += computed_qty
            total_vol += vol_val
                
            # Phân nhóm loài
            val = species.x_species_group or 'common'
            group_label = {
                'common': 'Thông thường',
                'precious': 'Danh mục loài nguy cấp, quý, hiếm',
                'cites': 'Phụ lục CITES'
            }.get(val, 'Thông thường')
            
            if wood_type == 'firewood':
                disp_vol = f"{dossier_line.volume_ster:.2f}".replace('.', ',') if dossier_line else f"{vol_val:.2f}".replace('.', ',')
                disp_qty = disp_vol
                disp_height = ""
                disp_diam = ""
                unit = 'Ster'
                vietnamese_unit_disp = "Ster"
                
                words_qty = number_to_vietnamese_words(int(round(vol_val)))
                words_vol = float_to_vietnamese_words(vol_val)
            else:
                disp_vol = format_volume_vietnamese(vol_val)
                disp_qty = f"{int(computed_qty):,}".replace('.', '.')
                disp_height = height_display
                disp_diam = dossier_line.diameter_display if dossier_line else ""
                unit = 'm³'
                vietnamese_unit_disp = "mét khối"
                
                words_qty = number_to_vietnamese_words(computed_qty)
                words_vol = float_to_vietnamese_words(vol_val)
            
            if words_qty:
                words_qty = words_qty[0].upper() + words_qty[1:]
            if words_vol:
                words_vol = words_vol[0].upper() + words_vol[1:]
                
            if wood_type == 'firewood':
                vietnamese_volume_unit = f"{words_vol.lower() if words_vol else ''} Ster"
            else:
                vietnamese_volume_unit = f"{words_vol.lower() if words_vol else ''} mét khối"
            if vietnamese_volume_unit:
                vietnamese_volume_unit = vietnamese_volume_unit.strip()
                vietnamese_volume_unit = vietnamese_volume_unit[0].upper() + vietnamese_volume_unit[1:]
                
            table_rows.append({
                'idx':           idx,
                'stt':           idx,
                'species_name':  species.name or "",
                'name_sci':      name_sci,
                'name_en':       name_en,
                'type':          group_label,
                'height':        disp_height,
                'diameter':      disp_diam,
                'volume':        disp_vol,
                'quantity':      disp_qty,
                'unit':          unit,
                'wood_type':     wood_type or 'wood',
            })
            
            species_lines.append({
                'wood_type': wood_type or 'wood',
                'species_label': "Củi" if wood_type == 'firewood' else "Gỗ",
                'species_name': species.name or "",
                'quantity': disp_qty,
                'volume': disp_vol,
                'species_volume': disp_vol,
                'vietnamese_quantity': words_qty,
                'vietnamese_quantity_lower': words_qty.lower() if words_qty else "",
                'vietnamese_volume': words_vol,
                'vietnamese_volume_unit': vietnamese_volume_unit,
                'unit': unit,
                'vietnamese_unit': vietnamese_unit_disp,
            })
            idx += 1
            
        main_species = ", ".join(list(set([x['species_name'] for x in table_rows])))
        
        # Nhóm loài tổng hợp của các dòng trên xe
        groups = []
        for x in table_rows:
            groups.append(x['type'])
        main_type = ", ".join(list(set(groups))) if groups else "Thông thường"
        
        total_volume_str = self._format_total_volume(wood_vol, firewood_vol)

        has_firewood = firewood_vol > 0
        disp_firewood_ster = f"{firewood_vol:.2f}".replace('.', ',') if has_firewood else ""
        vietnamese_firewood_qty = number_to_vietnamese_words(int(round(firewood_vol))) if has_firewood else ""

        fallback_vietnamese_volume_unit = species_lines[0]['vietnamese_volume_unit'] if species_lines else ""
        fallback_vietnamese_unit = species_lines[0]['vietnamese_unit'] if species_lines else ""

        # Tạo context đầy đủ tương tự _prepare_bkls_context nhưng các giá trị theo xe
        context = {
            # Bảng kê lâm sản
            'bkls_number':            d.x_bkls_number or "",
            'bkls_code':              d.x_bkls_number or "",
            'vietnamese_bkls_date':   vietnamese_ticket_date,
            'vietnamses_bkls_date':   vietnamese_ticket_date, # Dự phòng lỗi chính tả trong template
            'forest_owner_city':      forest_owner_city,

            # Bên mua
            'company_name':           company_info.get('company_name', ''),
            'company_address':        company_info.get('company_address', ''),
            'company_tax_number':     company_info.get('company_tax_number', ''),
            
            # Chủ rừng (Bên bán)
            'forest_owner_name':      owner_info.get('owner_name', ''),
            'forest_owner_address':   owner_info.get('owner_address', ''),
            'forset_owner_address':   owner_info.get('owner_address', ''), # dự phòng lỗi chính tả cũ
            'forest_owner_cccd':      owner_info.get('owner_cccd', ''),
            'forset_owner_cccd':      owner_info.get('owner_cccd', ''), # dự phòng lỗi chính tả cũ
            
            # Địa điểm & Thời gian
            'exploitation_address':   d._get_exploitation_address(),
            'exploitation_count_day': count_days,
            'delivery_count_day':     delivery_days,
            'vietnamese_exploitation_from_date': date_to_vietnamese_text(d.x_start_date),
            'vietnamese_exploitation_to_date':   date_to_vietnamese_text(d.x_end_date),
            'vietnamese_x_delivery_start_date': date_to_vietnamese_text(d.x_delivery_start_date),
            'vietnamese_x_delivery_end_date':   date_to_vietnamese_text(d.x_delivery_end_date),
            
            # Thông tin vận chuyển xe cụ thể
            'license_plate':          v_name,
            'vehicle_capacity':       f"{int(round(capacity)):,}".replace(',', '.'),
            'vehicle_volume':         f"{int(round(v_target_vol)):,}".replace(',', '.'),
            
            # Đường kính cực trị
            'diameter_min':           dia_min,
            'diameter_max':           dia_max,
            'diametter_max':          dia_max, # dự phòng lỗi chính tả cũ
            
            # Nhóm loài & Loại lâm sản
            'species_name':           main_species,
            'species_type':           main_type,
            'species_volume':         format_volume_vietnamese(wood_vol),
            # Củi xuất theo Ster
            'firewood_ster':          disp_firewood_ster,
            'firewood_quantity':      disp_firewood_ster,   # tương thích template cũ
            'firewood_volume':        disp_firewood_ster,   # tương thích template cũ
            
            # Số lượng và thể tích tổng hợp (chỉ gỗ)
            'total_quantity':         f"{int(wood_qty):,}".replace(',', '.'),
            'total_volume':           total_volume_str,
            'quantity':               f"{int(wood_qty):,}".replace(',', '.'),
            
            # Đọc số thành chữ tiếng Việt chuẩn xác
            'vietnamese_quantity':    number_to_vietnamese_words(wood_qty),
            'vietnamese_volume':      float_to_vietnamese_words(wood_vol),
            'vietnamese_firewood_quantity': vietnamese_firewood_qty,
            'vietnamese_firewood_volume':   vietnamese_firewood_qty,
            'vietnamese_firewood_ster':     vietnamese_firewood_qty,
            
            # Danh sách dòng bảng
            'table_rows':             table_rows,
            'species_lines':          species_lines,

            # Fallback variables
            'vietnamese_volume_unit':   fallback_vietnamese_volume_unit,
            'vietnamese_unit':          fallback_vietnamese_unit,
        }
        return context

    def _render_cn_bkls(self, template_source):
        """
        Render Bảng kê lâm sản chia nhỏ (cn_bkls):
        - Với mỗi chuyến xe (ticket), xác định ngày vận chuyển nằm trong khoảng x_start_date và x_end_date.
        - Với mỗi xe trong chuyến xe đó, lấy tải trọng từ x_vehicle_capacities và nhân với fill_rate.
        - Phân bổ chi tiết các loài gỗ/củi tuần tự cuốn chiếu cho từng xe.
        - Render ra các file docx riêng lẻ và ghép chúng lại thành một file docx duy nhất.
        """
        import datetime
        import io
        from docx import Document
        from docxtpl import DocxTemplate
        from odoo.exceptions import UserError
        
        d = self.dossier
        tickets = d.ticket_ids.sorted(key=lambda t: t.name)
        if not tickets:
            raise UserError(_("Hồ sơ chưa được tạo chuyến xe vận chuyển. Vui lòng bấm 'Sinh chuyến xe' trước khi xuất."))

        start_date = d.x_start_date or fields.Date.today()
        end_date = d.x_end_date or fields.Date.today()
        
        rendered_docs_bytes = []
        
        for trip_idx, ticket in enumerate(tickets):
            ticket_date = ticket.x_date
            if not ticket_date:
                ticket_date = start_date + datetime.timedelta(days=trip_idx)
                if ticket_date > end_date:
                    ticket_date = end_date
            
            # CƠ CHẾ MỚI: Sử dụng danh sách xe đã lưu x_vehicle_ids nếu có
            if ticket.x_vehicle_ids:
                vehicles_grouped = []
                seen_v_names = {}
                for v_line in ticket.x_vehicle_ids:
                    v_name = v_line.name or "Chưa có biển số"
                    if v_name not in seen_v_names:
                        seen_v_names[v_name] = len(vehicles_grouped)
                        vehicles_grouped.append({
                            'name': v_name,
                            'capacity': v_line.capacity,
                            'volume': 0.0,
                            'lines': []
                        })
                    v_idx = seen_v_names[v_name]
                    vehicles_grouped[v_idx]['lines'].append({
                        'species_id': v_line.species_id,
                        'wood_type': v_line.wood_type,
                        'volume': v_line.volume,
                    })
                    vehicles_grouped[v_idx]['volume'] += v_line.volume

                for v_idx, v_data in enumerate(vehicles_grouped, 1):
                    v_name = v_data['name']
                    capacity = v_data['capacity']
                    v_target_vol = round(v_data['volume'], 2)
                    v_lines = v_data['lines']

                    context = self._prepare_cn_bkls_context_for_vehicle(
                        ticket, v_name, capacity, v_target_vol, v_lines, ticket_date
                    )
                    context = self._add_context_helpers(context)
                    doc = DocxTemplate(template_source)
                    doc.render(context)
                    v_io = io.BytesIO()
                    doc.save(v_io)
                    rendered_docs_bytes.append(v_io.getvalue())

            else:
                # CƠ CHẾ FALLBACK (Tương thích ngược cho dữ liệu cũ)
                remaining_lines = []
                for line in ticket.ticket_line_ids:
                    remaining_lines.append({
                        'species_id': line.species_id,
                        'wood_type': line.wood_type,
                        'volume': line.volume,
                    })
                    
                if ticket.x_vehicle_capacities:
                    capacities = [float(x.strip()) for x in ticket.x_vehicle_capacities.split(',') if x.strip()]
                else:
                    avg_cap = (ticket.total_volume / ticket.vehicle_count) if ticket.vehicle_count > 0 else 20.0
                    capacities = [avg_cap] * (ticket.vehicle_count or 1)
                    
                for v_idx, capacity in enumerate(capacities, 1):
                    v_target_vol = round(capacity * (ticket.fill_rate or 1.0), 2)
                    if v_target_vol <= 0.0:
                        continue
                        
                    v_lines = []
                    remaining_v_vol = v_target_vol
                    
                    for line in remaining_lines:
                        if remaining_v_vol <= 0.0:
                            break
                        if line['volume'] > 0:
                            take = round(min(line['volume'], remaining_v_vol), 1)
                            if take > 0:
                                v_lines.append({
                                    'species_id': line['species_id'],
                                    'wood_type': line['wood_type'],
                                    'volume': take
                                })
                                line['volume'] = round(line['volume'] - take, 1)
                                remaining_v_vol = round(remaining_v_vol - take, 1)
                    
                    if remaining_v_vol > 0.0 and v_lines:
                        v_lines[-1]['volume'] = round(v_lines[-1]['volume'] + remaining_v_vol, 1)
                    elif remaining_v_vol < 0.0 and v_lines:
                        v_lines[-1]['volume'] = round(max(0.1, v_lines[-1]['volume'] + remaining_v_vol), 1)
                        
                    v_name = f"Xe {v_idx:02d}"
                    context = self._prepare_cn_bkls_context_for_vehicle(
                        ticket, v_name, capacity, v_target_vol, v_lines, ticket_date
                    )
                    context = self._add_context_helpers(context)
                    doc = DocxTemplate(template_source)
                    doc.render(context)
                    v_io = io.BytesIO()
                    doc.save(v_io)
                    rendered_docs_bytes.append(v_io.getvalue())
                
        if not rendered_docs_bytes:
            raise UserError(_("Không có dữ liệu chuyến xe hợp lệ để xuất bảng kê chia nhỏ."))
            
        return self._merge_docx_files(rendered_docs_bytes)

    def _paragraph_text(self, paragraph_el):
        """Lấy toàn bộ text trong một phần tử w:p."""
        return ''.join(t.text or '' for t in paragraph_el.xpath('.//w:t'))

    def _sanitize_docx_bytes_for_merge(self, doc_bytes, remove_page_breaks=True):
        """
        Chuẩn hóa từng phiếu trước khi ghép để tránh trang trống:
        - Giữ nguyên w:sectPr ở cuối body (để docx/docxcompose nhận diện đúng section)
        - Bỏ đoạn văn trống ở cuối trước w:sectPr
        - Bỏ ngắt trang trong nội dung của từng phiếu đơn lẻ nếu remove_page_breaks=True
          (mặc định True khi sanitize trước khi ghép — tránh ngắt trang trong nội dung phiếu)
          (đặt False khi gọi sau khi đã ghép — bảo toàn ngắt trang giữa các phiếu)
        """
        from docx import Document
        from docx.oxml.ns import qn

        doc = Document(io.BytesIO(doc_bytes))
        body = doc.element.body

        # Chỉ xóa page break trong nội dung khi xử lý từng phiếu đơn lẻ
        if remove_page_breaks:
            for paragraph in body.xpath('w:p'):
                p_pr = paragraph.find(qn('w:pPr'))
                if p_pr is not None:
                    for child in list(p_pr):
                        if child.tag in (qn('w:pageBreakBefore'), qn('w:pageBreakAfter')):
                            p_pr.remove(child)
                for br in paragraph.xpath('.//w:br'):
                    if br.get(qn('w:type')) == 'page':
                        parent = br.getparent()
                        if parent is not None:
                            parent.remove(br)

        for t_idx, table in enumerate(body.xpath('w:tbl')):
            if t_idx == 0:  # Chỉ thực hiện sanitize cho bảng hàng hóa đầu tiên (tránh xoá dòng trống ký tên ở bảng 2)
                for row in list(table.xpath('w:tr')):
                    texts = row.xpath('.//w:t/text()')
                    if not any((text or '').strip() for text in texts):
                        row.getparent().remove(row)

        # Xóa các đoạn văn trống ở cuối body, bỏ qua w:sectPr ở cuối cùng
        while len(body) > 0:
            last_idx = len(body) - 1
            if body[last_idx].tag.endswith('sectPr'):
                last_idx -= 1
            if last_idx < 0:
                break
            last = body[last_idx]
            tag = last.tag.split('}')[-1] if '}' in last.tag else last.tag
            if tag == 'p' and not self._paragraph_text(last).strip():
                body.remove(last)
                continue
            break

        out_io = io.BytesIO()
        doc.save(out_io)
        return out_io.getvalue()

    def _insert_page_break_paragraph(self, doc):
        """Thêm đúng một ngắt trang giữa hai phiếu."""
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn

        paragraph = doc.add_paragraph()
        run = paragraph.add_run()
        br = OxmlElement('w:br')
        br.set(qn('w:type'), 'page')
        run._r.append(br)

    def _merge_docx_files(self, files_bytes_list):
        """Ghép các file .docx thành một file (ưu tiên docxcompose)."""
        if not files_bytes_list:
            return b""
        if len(files_bytes_list) == 1:
            return self._sanitize_docx_bytes_for_merge(files_bytes_list[0])

        sanitized_list = [
            self._sanitize_docx_bytes_for_merge(doc_bytes)
            for doc_bytes in files_bytes_list
        ]

        try:
            from docx import Document
            from docxcompose.composer import Composer

            master = Document(io.BytesIO(sanitized_list[0]))
            composer = Composer(master)
            for file_bytes in sanitized_list[1:]:
                self._insert_page_break_paragraph(composer.doc)
                composer.append(Document(io.BytesIO(file_bytes)))
            out_io = io.BytesIO()
            composer.save(out_io)
            # KHÔNG gọi _sanitize lần 2 sau khi đã ghép — bảo toàn page break giữa các phiếu
            _logger.info(
                "[Renderer] Ghép %d file docx bằng docxcompose — mỗi phiếu 1 trang.",
                len(files_bytes_list),
            )
            return out_io.getvalue()
        except ImportError:
            _logger.warning(
                "[Renderer] docxcompose chưa cài — dùng phương thức ghép python-docx."
            )
            return self._merge_docx_files_legacy(sanitized_list)

    def _merge_docx_files_legacy(self, files_bytes_list):
        """Ghép docx thủ công (fallback khi không có docxcompose)."""
        from docx import Document
        if not files_bytes_list:
            return b""

        master_doc = Document(io.BytesIO(files_bytes_list[0]))
        for file_bytes in files_bytes_list[1:]:
            self._insert_page_break_paragraph(master_doc)
            sub_doc = Document(io.BytesIO(file_bytes))
            for element in sub_doc.element.body:
                if element.tag.endswith('sectPr'):
                    continue
                master_doc.element.body.append(element)

        out_io = io.BytesIO()
        master_doc.save(out_io)
        return out_io.getvalue()
