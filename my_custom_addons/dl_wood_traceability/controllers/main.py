# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import requests
import json
import io

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
