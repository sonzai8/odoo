# -*- coding: utf-8 -*-
import io
import re
import base64
import logging
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
    PYMUPDF_OK = True
except ImportError:
    PYMUPDF_OK = False

try:
    import pytesseract
    from PIL import Image
    TESSERACT_OK = True
except ImportError:
    TESSERACT_OK = False


class DlDigitizeContractWizard(models.TransientModel):
    """
    Wizard Số hoá Hợp đồng Hàng loạt:
    1. upload  → Người dùng upload tối đa 20 file PDF cùng lúc
    2. review  → Hệ thống OCR từng file, hiển thị bảng kết quả để người dùng sửa đổi
    3. done    → Lưu hàng loạt vào hồ sơ nhân viên (tạo mới/gắn hồ sơ cũ)
    """
    _name = 'dl.digitize.contract.wizard'
    _description = 'Số hoá Hợp đồng Hàng loạt'

    # ─── Trạng thái wizard ────────────────────────────────────────────────────
    state = fields.Selection([
        ('upload', 'Bước 1: Upload PDF'),
        ('review', 'Bước 2: Kiểm tra thông tin'),
        ('done',   'Hoàn thành'),
    ], default='upload', string='Trạng thái')

    # ─── Step 1: Upload Hàng loạt ──────────────────────────────────────────────
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'dl_digitize_contract_wizard_attachment_rel',
        'wizard_id',
        'attachment_id',
        string='Files PDF hợp đồng',
    )

    doc_type = fields.Selection([
        ('contract', 'Hợp đồng lao động'),
        ('id_card',  'CCCD / CMND'),
        ('decision', 'Quyết định'),
        ('other',    'Tài liệu khác'),
    ], string='Loại tài liệu', default='contract', required=True)
    doc_note = fields.Char(string='Ghi chú chung')

    # ─── Step 2: Review (Bảng chi tiết kết quả OCR) ──────────────────────────
    line_ids = fields.One2many(
        'dl.digitize.contract.wizard.line',
        'wizard_id',
        string='Chi tiết kết quả OCR',
    )

    # ─── Step 3: Done ──────────────────────────────────────────────────────────
    result_message = fields.Text(string='Kết quả xử lý', readonly=True)

    # ──────────────────────────────────────────────────────────────────────────
    # BƯỚC 1 → 2: Chạy OCR cho toàn bộ file
    # ──────────────────────────────────────────────────────────────────────────

    def action_process_ocr(self):
        """Đọc danh sách file → Chạy OCR từng file → Tạo line cho bước Review."""
        self.ensure_one()

        if not PYMUPDF_OK:
            raise UserError(_(
                'Thư viện PyMuPDF (pymupdf) chưa được cài đặt.\n'
                'Vui lòng chạy: pip install pymupdf'
            ))
        if not TESSERACT_OK:
            raise UserError(_(
                'Thư viện pytesseract hoặc Pillow chưa được cài đặt.\n'
                'Vui lòng chạy: pip install pytesseract Pillow'
            ))

        if not self.attachment_ids:
            raise UserError(_('Vui lòng tải lên ít nhất một file PDF.'))

        if len(self.attachment_ids) > 20:
            raise UserError(_('Hệ thống chỉ hỗ trợ số hoá tối đa 20 file cùng lúc để đảm bảo hiệu năng.'))

        lines_vals = []
        for idx, attach in enumerate(self.attachment_ids):
            _logger.info("Bắt đầu OCR file %d/%d: %s", idx + 1, len(self.attachment_ids), attach.name)
            
            try:
                # 1) Giải mã file PDF
                pdf_bytes = base64.b64decode(attach.datas) if attach.datas else b''
                if not pdf_bytes:
                    lines_vals.append({
                        'attachment_id': attach.id,
                        'status': 'failed',
                        'message': 'File không có dữ liệu.',
                    })
                    continue

                # 2) OCR
                ocr_text = self._run_ocr(pdf_bytes)
                if not ocr_text.strip():
                    lines_vals.append({
                        'attachment_id': attach.id,
                        'status': 'failed',
                        'message': 'Không thể trích xuất văn bản từ PDF.',
                    })
                    continue

                # 3) Trích xuất thông tin
                extracted = self._extract_info(ocr_text)

                # 4) Tìm nhân viên theo CCCD
                employee = False
                if extracted.get('cccd'):
                    employee = self.env['hr.employee'].search(
                        [('identification_id', '=', extracted['cccd'])], limit=1
                    )

                # 5) Tính độ tin cậy
                found_count = sum([
                    bool(extracted.get('cccd')),
                    bool(extracted.get('name')),
                    bool(extracted.get('dob')),
                ])
                if found_count == 3:
                    confidence = 'high'
                elif found_count == 2:
                    confidence = 'medium'
                else:
                    confidence = 'low'

                # 6) Parse ngày sinh
                dob_date = False
                dob_str = extracted.get('dob')
                if dob_str:
                    for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y'):
                        try:
                            dob_date = datetime.strptime(dob_str, fmt).date()
                            break
                        except ValueError:
                            pass

                lines_vals.append({
                    'attachment_id': attach.id,
                    'extracted_cccd': extracted.get('cccd') or '',
                    'extracted_name': extracted.get('name') or '',
                    'extracted_dob': dob_date or False,
                    'ocr_confidence': confidence,
                    'matched_employee_id': employee.id if employee else False,
                    'action_type': 'link' if employee else 'create',
                    'status': 'pending',
                })

            except Exception as e:
                _logger.exception("OCR file thất bại: %s", attach.name)
                lines_vals.append({
                    'attachment_id': attach.id,
                    'status': 'failed',
                    'message': f'Lỗi hệ thống: {str(e)}',
                })

        # Cập nhật line_ids bằng Odoo command list để đồng bộ client-side cache sạch sẽ
        commands = [(5, 0, 0)]
        for vals in lines_vals:
            commands.append((0, 0, vals))

        self.write({
            'state': 'review',
            'line_ids': commands,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def _run_ocr(self, pdf_bytes: bytes) -> str:
        """Chuyển đổi các trang PDF đầu tiên sang ảnh rồi chạy Tesseract OCR."""
        doc = fitz.open(stream=pdf_bytes, filetype='pdf')
        all_text = []

        try:
            langs = pytesseract.get_languages()
            ocr_lang = 'vie+eng' if 'vie' in langs else 'eng'
        except Exception:
            ocr_lang = 'eng'

        # Xử lý tối đa 5 trang đầu của mỗi tài liệu để tối ưu tốc độ
        for page_num, page in enumerate(doc):
            if page_num >= 5:
                break
            # Render ở 250 DPI
            mat = fitz.Matrix(250 / 72, 250 / 72)
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
            img = Image.open(io.BytesIO(pix.tobytes('png')))
            try:
                page_text = pytesseract.image_to_string(img, lang=ocr_lang)
                all_text.append(page_text)
            except Exception as e:
                _logger.warning('OCR trang %d lỗi: %s', page_num + 1, e)

        doc.close()
        return '\n'.join(all_text)

    def _extract_info(self, text: str) -> dict:
        """Trích xuất thông tin CCCD, họ tên, ngày sinh bằng Regex."""
        result = {}

        # ── CCCD / CMND (9 hoặc 12 chữ số) ──
        cccd_patterns = [
            r'(?:CMT|CMND|CCCD|C\.C\.C\.D)\s*[:/\s]+(\d{9,12})',
            r'(?:Số\s+)?(?:CMT|CMND|CCCD)\s*[:\-]?\s*(\d{9,12})',
        ]
        for pat in cccd_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                result['cccd'] = m.group(1).strip()
                break

        # ── Họ và tên ──
        name_patterns = [
            r'Bên\s+B\s*[:\-]?\s*(?:Ông\s*/?\s*)?(?:Bà\s*)?[:\-]?\s*([A-ZÀ-Ỹ][A-Za-zÀ-ỹ\s]{2,49})',
            r'BÊN\s+B\s*\([^)]+\)\s*:\s*([A-ZÀ-Ỹ][A-Za-zÀ-ỹ\s]{2,49})',
            r'B[e\xe9\xea]n\s+B\s*[:\-]?\s*(?:[Oo]ng\s*/?\s*)?[Bb][a\xe0\xe2]?\s*[:\-]?\s*([A-Z][A-Za-z\s]{2,49})',
            r'BEN\s+B\s*\([^)]+\)\s*:\s*([A-Z][A-Za-z\s]{2,49})',
        ]
        for pat in name_patterns:
            m = re.search(pat, text)
            if m:
                name_raw = m.group(1).strip()
                name_clean = name_raw.split('\n')[0].strip()
                words = name_clean.split()
                if 1 <= len(words) <= 5:
                    result['name'] = ' '.join(words)
                    break

        # ── Ngày sinh ──
        dob_patterns = [
            r'(?:Sinh\s+ngày|Ngày\s+sinh|Ngày\s+tháng\s+năm\s+sinh)\s*[:\-]?\s*(\d{1,2}[/\.\-]\d{1,2}[/\.\-]\d{4})',
            r'(?:Sinh\s+ngay|Ngay\s+thang\s+nam\s+sinh|Ngay\s+sinh)\s*[:\-]?\s*(\d{1,2}[/\.\-]\d{1,2}[/\.\-]\d{4})',
            r'sinh[^\n]{0,30}?(\d{1,2}[/\.\-]\d{1,2}[/\.\-]\d{4})',
        ]
        for pat in dob_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                result['dob'] = m.group(1).replace('.', '/').replace('-', '/')
                break

        return result

    # ──────────────────────────────────────────────────────────────────────────
    # BƯỚC 2 → 3: Xác nhận lưu hàng loạt
    # ──────────────────────────────────────────────────────────────────────────

    def action_confirm_save(self):
        """Xử lý từng dòng: Tìm/Tạo nhân viên và gắn tài liệu scan."""
        self.ensure_one()

        if not self.line_ids:
            raise UserError(_('Không có tài liệu nào để xử lý.'))

        success_count = 0
        failed_count = 0
        created_count = 0
        linked_count = 0

        for line in self.line_ids:
            # Skip những dòng đã lỗi từ khâu OCR trước đó
            if line.status == 'failed' and not line.pdf_file:
                failed_count += 1
                continue

            try:
                # Kiểm tra thông tin tối thiểu
                cccd = line.extracted_cccd
                name = line.extracted_name

                if not cccd and not name:
                    line.write({
                        'status': 'failed',
                        'message': 'Lỗi: Thiếu thông tin cả Số CCCD và Họ tên.',
                    })
                    failed_count += 1
                    continue

                # Tìm nhân viên
                employee = False
                if cccd:
                    employee = self.env['hr.employee'].search(
                        [('identification_id', '=', cccd)], limit=1
                    )

                created_new = False
                if not employee:
                    # Nếu chưa có nhân viên và không nhập tên
                    if not name:
                        line.write({
                            'status': 'failed',
                            'message': 'Lỗi: Không tìm thấy nhân viên và thiếu Họ tên để tạo mới.',
                        })
                        failed_count += 1
                        continue

                    # Tạo nhân viên mới
                    employee_vals = {'name': name}
                    if cccd:
                        employee_vals['identification_id'] = cccd
                    if line.extracted_dob:
                        employee_vals['birthday'] = line.extracted_dob
                    
                    employee = self.env['hr.employee'].create(employee_vals)
                    created_new = True
                    created_count += 1
                else:
                    linked_count += 1

                # Tạo tài liệu scan
                doc_name = (
                    f'HĐ scan - {employee.name} - '
                    f'{fields.Date.today().strftime("%d/%m/%Y")}'
                )
                self.env['dl.employee.scan.doc'].create({
                    'employee_id': employee.id,
                    'name': doc_name,
                    'file_data': line.pdf_file,
                    'file_name': line.pdf_filename or 'hop_dong_scan.pdf',
                    'doc_type': self.doc_type,
                    'upload_date': fields.Date.today(),
                    'note': self.doc_note or '',
                    'x_is_digitized': True,
                })

                line.write({
                    'matched_employee_id': employee.id,
                    'status': 'success',
                    'message': 'Đã tạo nhân viên mới và lưu file.' if created_new else 'Đã lưu file vào hồ sơ nhân viên có sẵn.',
                })
                success_count += 1

            except Exception as e:
                _logger.exception("Lỗi khi lưu kết quả dòng: %s", line.pdf_filename)
                line.write({
                    'status': 'failed',
                    'message': f'Lỗi hệ thống: {str(e)}',
                })
                failed_count += 1

        result_msg = (
            f"🎉 Hoàn thành xử lý tài liệu:\n"
            f"- Thành công: {success_count} file\n"
            f"  + Tạo mới nhân viên: {created_count} người\n"
            f"  + Gắn vào nhân viên cũ: {linked_count} người\n"
            f"- Thất bại: {failed_count} file"
        )

        self.write({
            'state': 'done',
            'result_message': result_msg,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def action_back_to_upload(self):
        """Quay lại bước upload."""
        self.write({'state': 'upload'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }


class DlDigitizeContractWizardLine(models.TransientModel):
    """Chi tiết từng file được xử lý OCR và lưu thông tin tương ứng."""
    _name = 'dl.digitize.contract.wizard.line'
    _description = 'Chi tiết Số hoá Hợp đồng'

    wizard_id = fields.Many2one(
        'dl.digitize.contract.wizard',
        string='Wizard chính',
        ondelete='cascade',
        required=True,
    )
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='File gốc',
        ondelete='cascade',
    )
    pdf_filename = fields.Char(
        related='attachment_id.name',
        string='Tên file',
        readonly=True,
    )
    pdf_file = fields.Binary(
        related='attachment_id.datas',
        string='Dữ liệu file',
        readonly=True,
    )

    # Dữ liệu trích xuất (cho phép sửa đổi)
    extracted_cccd = fields.Char(string='Số CCCD / CMND')
    extracted_name = fields.Char(string='Họ và tên')
    extracted_dob = fields.Date(string='Ngày sinh')

    ocr_confidence = fields.Selection([
        ('high',   '✅ Cao'),
        ('medium', '⚠️ Trung bình'),
        ('low',    '❌ Thấp'),
    ], string='Độ tin cậy', readonly=True)

    # Trạng thái khớp
    matched_employee_id = fields.Many2one(
        'hr.employee',
        string='Nhân viên khớp',
        help='Nhân viên khớp theo CCCD. Bạn có thể chọn lại nếu hệ thống khớp sai hoặc chưa khớp.',
    )
    action_type = fields.Selection([
        ('link',   'Gắn vào hồ sơ cũ'),
        ('create', 'Tạo hồ sơ mới'),
    ], string='Hành động dự kiến')

    # Trạng thái lưu
    status = fields.Selection([
        ('pending', 'Chờ xử lý'),
        ('success', 'Thành công'),
        ('failed',  'Thất bại'),
    ], default='pending', string='Trạng thái', readonly=True)
    message = fields.Char(string='Ghi chú/Lỗi', readonly=True)

    @api.onchange('extracted_cccd')
    def _onchange_extracted_cccd(self):
        """Khi người dùng sửa CCCD, tìm lại nhân viên tương ứng."""
        if self.extracted_cccd:
            employee = self.env['hr.employee'].search(
                [('identification_id', '=', self.extracted_cccd)], limit=1
            )
            if employee:
                self.matched_employee_id = employee.id
                self.action_type = 'link'
            else:
                self.matched_employee_id = False
                self.action_type = 'create'
        else:
            self.matched_employee_id = False
            self.action_type = 'create'

    def action_open_employee(self):
        """Nút bấm mở nhanh hồ sơ nhân viên đã xử lý."""
        self.ensure_one()
        if not self.matched_employee_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee',
            'view_mode': 'form',
            'res_id': self.matched_employee_id.id,
            'target': '_blank',  # Mở tab mới
        }
