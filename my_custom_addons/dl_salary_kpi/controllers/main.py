from odoo import http
from odoo.http import request
import base64
import logging

_logger = logging.getLogger(__name__)

class DlSalaryKpiController(http.Controller):

    @http.route('/dl_salary_kpi/preview_pdf/<int:history_id>', type='http', auth='user')
    def preview_salary_pdf(self, history_id, **kwargs):
        """Convert file gốc thành PDF qua LibreOffice và trả về trình duyệt"""
        history = request.env['dl.salary.kpi.document.history'].sudo().browse(history_id)
        if not history.exists() or not history.file:
            return request.not_found()

        try:
            file_content = base64.b64decode(history.file)
            extension = history.file_name.split('.')[-1].lower() if history.file_name else ''
            
            if extension == 'pdf':
                pdf_content = file_content
            else:
                pdf_content = history._convert_to_pdf(file_content, extension)
                if not pdf_content:
                    return "Lỗi: Không thể convert file này sang PDF."
            
            filename = history.file_name or "Tài_liệu"
            if '.' in filename:
                filename = filename.rsplit('.', 1)[0] + '.pdf'
            else:
                filename += '.pdf'

            return request.make_response(
                pdf_content,
                headers=[
                    ('Content-Type', 'application/pdf'),
                    ('Content-Disposition', f'inline; filename="{filename}"'),
                    ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                ]
            )
        except Exception as e:
            _logger.error("Lỗi khi Preview PDF trong dl_salary_kpi: %s", str(e))
            return f"Lỗi hệ thống khi xem trước PDF: {str(e)}"
