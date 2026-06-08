# -*- coding: utf-8 -*-
import base64
import logging
import os
import subprocess
import tempfile

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class DlContractTemplateController(http.Controller):
    """Controller xử lý xem trước file template hợp đồng Word (.docx)
    
    Quy trình:
    1. Lấy record dl.contract.template theo ID
    2. Giải mã file .docx từ trường binary
    3. Dùng LibreOffice chuyển đổi .docx → .pdf
    4. Trả về file PDF với Content-Disposition: inline để browser hiển thị trực tiếp
    """

    @http.route(
        '/dl_contract/preview_template/<int:template_id>',
        type='http',
        auth='user',
        methods=['GET'],
    )
    def preview_template(self, template_id, **kwargs):
        """Chuyển đổi file template .docx sang PDF và trả về để xem trước trên trình duyệt."""
        # Kiểm tra quyền truy cập
        template = request.env['dl.contract.template'].browse(template_id)
        if not template.exists():
            return request.make_response(
                '<h3>Không tìm thấy template!</h3>',
                headers=[('Content-Type', 'text/html; charset=utf-8')]
            )

        if not template.template_file:
            return request.make_response(
                '<h3>Template chưa có file đính kèm. Vui lòng upload file .docx trước.</h3>',
                headers=[('Content-Type', 'text/html; charset=utf-8')]
            )

        try:
            # Giải mã file docx từ base64
            docx_data = base64.b64decode(template.template_file)

            # Tạo thư mục tạm để làm việc
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Ghi file .docx ra đĩa tạm
                docx_filename = template.template_filename or 'template.docx'
                # Đảm bảo tên file có đuôi .docx
                if not docx_filename.lower().endswith('.docx'):
                    docx_filename += '.docx'

                input_path = os.path.join(tmp_dir, _safe_ascii_filename(docx_filename) + '.docx')
                with open(input_path, 'wb') as f:
                    f.write(docx_data)

                # Chạy LibreOffice để convert sang PDF
                # Lệnh: libreoffice --headless --convert-to pdf <file> --outdir <dir>
                libreoffice_cmd = _find_libreoffice()
                if not libreoffice_cmd:
                    # LibreOffice không có: trả về file .docx để download
                    safe_filename = _safe_ascii_filename(docx_filename)
                    return request.make_response(
                        docx_data,
                        headers=[
                            ('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
                            ('Content-Disposition', f'attachment; filename="{safe_filename}"'),
                        ]
                    )

                result = subprocess.run(
                    [libreoffice_cmd, '--headless', '--convert-to', 'pdf', input_path, '--outdir', tmp_dir],
                    capture_output=True,
                    timeout=30,
                )

                if result.returncode != 0:
                    _logger.error(
                        "LibreOffice conversion failed for template %s: %s",
                        template_id,
                        result.stderr.decode('utf-8', errors='replace')
                    )
                    # Fallback: trả file docx để download
                    safe_filename = _safe_ascii_filename(docx_filename)
                    return request.make_response(
                        docx_data,
                        headers=[
                            ('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
                            ('Content-Disposition', f'attachment; filename="{safe_filename}"'),
                        ]
                    )

                # Tìm file PDF output (LibreOffice tạo file .pdf cùng tên với file input)
                safe_docx_base = _safe_ascii_filename(docx_filename)
                pdf_filename = safe_docx_base + '.pdf'
                pdf_path = os.path.join(tmp_dir, pdf_filename)

                if not os.path.exists(pdf_path):
                    _logger.error("PDF output not found after conversion: %s", pdf_path)
                    return request.make_response(
                        '<h3>Lỗi chuyển đổi file. Vui lòng thử tải xuống thủ công.</h3>',
                        headers=[('Content-Type', 'text/html; charset=utf-8')]
                    )

                # Đọc PDF và trả về với inline display
                with open(pdf_path, 'rb') as f:
                    pdf_data = f.read()

                # Dùng thẳng tên file gốc (đã là ASCII) cho Content-Disposition
                pdf_output_name = os.path.splitext(docx_filename)[0] + '.pdf'
                return request.make_response(
                    pdf_data,
                    headers=[
                        ('Content-Type', 'application/pdf'),
                        ('Content-Disposition', f'inline; filename="{pdf_output_name}"'),
                        ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                    ]
                )

        except subprocess.TimeoutExpired:
            _logger.error("LibreOffice conversion timeout for template %s", template_id)
            return request.make_response(
                '<h3>Quá thời gian chuyển đổi. Vui lòng thử lại hoặc tải xuống file để xem.</h3>',
                headers=[('Content-Type', 'text/html; charset=utf-8')]
            )
        except Exception as e:
            _logger.exception("Unexpected error in preview_template for template %s: %s", template_id, e)
            return request.make_response(
                f'<h3>Đã xảy ra lỗi: {str(e)}</h3>',
                headers=[('Content-Type', 'text/html; charset=utf-8')]
            )


def _safe_ascii_filename(name: str) -> str:
    """Chuyển tên file về ASCII thuần để dùng trong HTTP header.
    
    HTTP headers (latin-1) không chấp nhận ký tự Unicode.
    Thay thế ký tự non-ASCII bằng dấu gạch dưới.
    """
    import unicodedata
    # Normalize unicode (decompose accented chars)
    normalized = unicodedata.normalize('NFKD', name)
    # Encode sang ASCII, bỏ các ký tự không encode được
    ascii_bytes = normalized.encode('ascii', errors='ignore')
    ascii_str = ascii_bytes.decode('ascii')
    # Xoá các ký tự không hợp lệ trong tên file
    safe = ''.join(c if c.isalnum() or c in (' ', '-', '_', '.') else '_' for c in ascii_str)
    return safe.strip() or 'template'


def _find_libreoffice():
    """Tìm đường dẫn tới LibreOffice trên hệ thống.
    
    Kiểm tra các vị trí phổ biến trên Linux/macOS.
    Trả về None nếu không tìm thấy.
    """
    candidates = [
        'libreoffice',          # Có trong PATH (Linux Debian)
        'soffice',              # Alias phổ biến
        '/usr/bin/libreoffice',
        '/usr/bin/soffice',
        '/usr/lib/libreoffice/program/soffice',
        '/opt/libreoffice/program/soffice',
        # macOS
        '/Applications/LibreOffice.app/Contents/MacOS/soffice',
    ]
    for cmd in candidates:
        try:
            result = subprocess.run(
                [cmd, '--version'],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                return cmd
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None
