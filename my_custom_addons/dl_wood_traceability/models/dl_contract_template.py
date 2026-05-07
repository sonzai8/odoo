# -*- coding: utf-8 -*-
import os
import base64
from odoo import models, fields, api, _
from odoo.modules import get_module_path

class DlWoodContractTemplate(models.Model):
    _name = 'dl.wood.contract.template'
    _description = 'Mẫu hợp đồng khách hàng'

    name = fields.Char(string='Tên mẫu hợp đồng', required=True)
    partner_id = fields.Many2one('res.partner', string='Khách hàng', required=True, ondelete='cascade')
    file_url = fields.Char(string='Đường dẫn file', readonly=True)
    file_upload = fields.Binary(string='Tải lên file (.doc/.docx)', store=False)
    file_name = fields.Char(string='Tên file')

    def action_download_file(self):
        """Action để tải file về từ server"""
        self.ensure_one()
        if not self.file_url:
            return False
        
        # Đường dẫn vật lý trên server
        base_path = get_module_path('dl_wood_traceability')
        # Loại bỏ tiền tố module để lấy đường dẫn tương đối trong thư mục static
        relative_path = self.file_url.replace('/dl_wood_traceability/', '')
        full_path = os.path.join(base_path, relative_path)

        if os.path.exists(full_path):
            with open(full_path, 'rb') as f:
                data = base64.b64encode(f.read())
            
            attachment = self.env['ir.attachment'].create({
                'name': self.file_name or self.name,
                'datas': data,
                'res_model': self._name,
                'res_id': self.id,
                'type': 'binary',
            })
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'self',
            }
        return False

    @api.model_create_multi
    def create(self, vals_list):
        # Lưu trữ dữ liệu file tạm thời vì file_upload không lưu vào DB
        file_data_list = []
        for vals in vals_list:
            file_data = vals.pop('file_upload', False)
            file_name = vals.get('file_name', False)
            file_data_list.append((file_data, file_name))
        
        recs = super(DlWoodContractTemplate, self).create(vals_list)
        
        for rec, (data, name) in zip(recs, file_data_list):
            if data and name:
                rec._save_file_to_server(data, name)
        return recs

    def write(self, vals):
        file_data = vals.pop('file_upload', False)
        file_name = vals.get('file_name', False)
        
        res = super(DlWoodContractTemplate, self).write(vals)
        
        if file_data:
            for rec in self:
                # Nếu không có tên file mới trong vals, dùng tên file hiện tại của bản ghi
                name = file_name or rec.file_name
                if name:
                    rec._save_file_to_server(file_data, name)
        return res

    def _save_file_to_server(self, binary_data, file_name):
        """Lưu file vật lý lên thư mục static của module"""
        self.ensure_one()
        # Đường dẫn thư mục static/contracts
        base_path = get_module_path('dl_wood_traceability')
        contracts_path = os.path.join(base_path, 'static', 'contracts')
        
        # Tạo thư mục theo ID khách hàng để tránh trùng tên file
        partner_folder = os.path.join(contracts_path, str(self.partner_id.id))
        if not os.path.exists(partner_folder):
            os.makedirs(partner_folder, exist_ok=True)

        full_path = os.path.join(partner_folder, file_name)
        
        # Lưu file
        with open(full_path, 'wb') as f:
            f.write(base64.b64decode(binary_data))
        
        # Lưu URL tương đối để truy cập (Odoo static file mapping)
        url = f'/dl_wood_traceability/static/contracts/{self.partner_id.id}/{file_name}'
        self.sudo().write({'file_url': url, 'file_name': file_name})

    def unlink(self):
        """Xóa file vật lý khi xóa bản ghi"""
        for rec in self:
            if rec.file_url:
                base_path = get_module_path('dl_wood_traceability')
                relative_path = rec.file_url.replace('/dl_wood_traceability/', '')
                full_path = os.path.join(base_path, relative_path)
                if os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                    except:
                        pass
        return super(DlWoodContractTemplate, self).unlink()
