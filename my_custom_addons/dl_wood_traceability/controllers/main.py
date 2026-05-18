from odoo import http, fields
from odoo.http import request
import requests
import json
import io
import logging

# Import helper function từ renderer — tránh code trùng lặp
from odoo.addons.dl_wood_traceability.models.dl_wood_dossier_renderer import no_accent_vietnamese

_logger = logging.getLogger(__name__)


class WoodDossierController(http.Controller):

    @http.route('/dl_wood/download_attachment/<int:attachment_id>', type='http', auth='user')
    def download_woodpro_attachment(self, attachment_id, **kwargs):
        attachment = request.env['dl.wood.dossier.attachment'].sudo().browse(attachment_id)
        if not attachment.exists() or not attachment.file_type or not attachment.dossier_id.x_woodpro_id:
            return request.not_found()

        # Lấy cấu hình WoodPro
        config = request.env['dl.woodpro.config'].sudo().search([], limit=1)
        if not config or not config.token:
            return request.not_found()

        headers = {
            'Authorization': f'Bearer {config.token}',
            'Content-Type': 'application/json'
        }

        # API tải file POST
        base = config.base_url.rstrip('/')
        if base.endswith('/v1'):
            url = f"{base}/views/downloads"
        else:
            url = f"{base}/v1/views/downloads"

        payload = {
            "type": attachment.file_type,
            "miningId": attachment.dossier_id.x_woodpro_id,
            "parts": "1",
            "version": "tt262025"
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                res_data = response.json()
                file_url = res_data.get('result')
                
                if file_url:
                    # Chuyển hướng người dùng đến URL của file
                    return request.redirect(file_url, local=False)
                else:
                    return f"Lỗi: Không tìm thấy URL file trong phản hồi từ WoodPro: {res_data}"
            else:
                return f"Lỗi từ WoodPro API ({response.status_code}): {response.text}"
        except Exception as e:
            return f"Lỗi hệ thống khi tải file: {str(e)}"
    @http.route('/dl_wood/render_docx/<int:dossier_id>/<string:template_key>', type='http', auth='user')
    def render_wood_docx(self, dossier_id, template_key, **kwargs):
        """Render docx trực tiếp và trả về cho trình duyệt tải về"""
        dossier = request.env['dl.wood.dossier'].sudo().browse(dossier_id)
        if not dossier.exists():
            return request.not_found()

        try:
            file_content = dossier._render_docx(template_key)
            filename = dossier.get_export_filename(template_key)
            
            return request.make_response(
                file_content,
                headers=[
                    ('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
                    ('Content-Disposition', http.content_disposition(filename)),
                    ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                    ('Pragma', 'no-cache'),
                    ('Expires', '0')
                ]
            )
        except Exception as e:
            return f"Lỗi khi tạo file: {str(e)}"

    @http.route('/dl_wood/preview_pdf/<int:dossier_id>/<string:template_key>', type='http', auth='user')
    def preview_wood_pdf(self, dossier_id, template_key, **kwargs):
        """Render docx, convert sang PDF và trả về để xem trên trình duyệt"""
        dossier = request.env['dl.wood.dossier'].sudo().browse(dossier_id)
        if not dossier.exists():
            return request.not_found()

        try:
            # 1. Render DOCX
            docx_content = dossier._render_docx(template_key)
            
            # 2. Convert sang PDF
            pdf_content = dossier._convert_docx_to_pdf(docx_content)
            
            if not pdf_content:
                return "Lỗi: Không thể tạo file PDF."

            filename = dossier.get_export_filename(template_key).replace('.docx', '.pdf')
            
            return request.make_response(
                pdf_content,
                headers=[
                    ('Content-Type', 'application/pdf'),
                    ('Content-Disposition', f'inline; filename={filename}'),
                    ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                ]
            )
        except Exception as e:
            _logger.error("Lỗi khi Preview PDF: %s", str(e))
            return f"Lỗi khi xem trước PDF: {str(e)}"

    @http.route('/dl_wood/download_zip/<int:dossier_id>', type='http', auth='user')
    def download_wood_zip(self, dossier_id, **kwargs):
        """Nén các tài liệu đã chọn thành file ZIP"""
        import zipfile
        dossier = request.env['dl.wood.dossier'].sudo().browse(dossier_id)
        if not dossier.exists():
            return request.not_found()

        selected_docs = dossier.document_ids.filtered(lambda d: d.x_is_selected)
        if not selected_docs:
            return "Vui lòng chọn ít nhất một tài liệu."

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for doc in selected_docs:
                try:
                    file_content = dossier._render_docx(doc.template_key)
                    filename = dossier.get_export_filename(doc.template_key)
                    zip_file.writestr(filename, file_content)
                except Exception as e:
                    _logger.error("Lỗi khi nén file %s: %s", doc.name, e)

        zip_buffer.seek(0)
        zip_filename = f"HO_SO_GO_{no_accent_vietnamese(dossier.name)}_{fields.Date.today().strftime('%d%m%Y')}.zip"
        
        return request.make_response(
            zip_buffer.getvalue(),
            headers=[
                ('Content-Type', 'application/zip'),
                ('Content-Disposition', http.content_disposition(zip_filename)),
                ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                ('Pragma', 'no-cache'),
                ('Expires', '0')
            ]
        )
