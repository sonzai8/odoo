# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import io
import zipfile
import base64

class DlScanDocZipWizard(models.TransientModel):
    _name = 'dl.scan.doc.zip.wizard'
    _description = 'Tải Zip nhiều tài liệu scan'

    file_data = fields.Binary(string='File Zip', readonly=True)
    file_name = fields.Char(string='Tên file zip', readonly=True)
    count = fields.Integer(string='Số lượng file', readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super(DlScanDocZipWizard, self).default_get(fields_list)
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            raise UserError(_("Vui lòng chọn ít nhất một tài liệu scan để tải xuống."))
            
        docs = self.env['dl.employee.scan.doc'].browse(active_ids)
        
        # Tạo file zip trong bộ nhớ
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            used_filenames = set()
            for doc in docs:
                if not doc.file_data:
                    continue
                # Decode file data
                file_content = base64.b64decode(doc.file_data)
                
                # Tạo tên file độc nhất trong file zip
                base_name = doc.file_name or doc.name or 'file'
                if not base_name.lower().endswith('.pdf'):
                    base_name += '.pdf'
                
                # Đặt tên dạng {employee_name}_{base_name} để dễ nhận diện
                emp_name = (doc.employee_id.name or '').replace(' ', '_')
                filename = f"{emp_name}_{base_name}"
                
                # Tránh trùng tên trong zip
                original_filename = filename
                counter = 1
                while filename in used_filenames:
                    name_parts = original_filename.rsplit('.', 1)
                    if len(name_parts) == 2:
                        filename = f"{name_parts[0]}_{counter}.{name_parts[1]}"
                    else:
                        filename = f"{original_filename}_{counter}"
                    counter += 1
                    
                used_filenames.add(filename)
                zip_file.writestr(filename, file_content)
                
        zip_buffer.seek(0)
        zip_data = base64.b64encode(zip_buffer.read())
        
        res.update({
            'file_data': zip_data,
            'file_name': f"Tai_lieu_scan_{fields.Date.today().strftime('%Y%m%d')}.zip",
            'count': len(docs),
        })
        return res
