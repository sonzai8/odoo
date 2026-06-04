from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import os
import shutil
import tempfile
import subprocess

_logger = logging.getLogger(__name__)

class DlSalaryKpiDocumentHistory(models.Model):
    _name = 'dl.salary.kpi.document.history'
    _description = 'Lịch sử tài liệu bảng lương'
    _order = 'upload_date desc, id desc'

    month_id = fields.Many2one('dl.salary.kpi.month', string='Bảng lương', ondelete='cascade', required=True)
    name = fields.Char(string='Tên tài liệu', required=True)
    file_name = fields.Char(string='Tên file gốc')
    file = fields.Binary(string='File gốc', attachment=True, required=True)
    upload_date = fields.Datetime(string='Thời gian tải lên', default=fields.Datetime.now, required=True)
    upload_user_id = fields.Many2one('res.users', string='Người tải lên', default=lambda self: self.env.user, required=True)
    attachment_id = fields.Many2one('ir.attachment', string='Attachment gốc', ondelete='set null')

    def action_preview_pdf(self):
        """Mở tab mới gọi Controller để preview PDF"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/dl_salary_kpi/preview_pdf/{self.id}',
            'target': 'new'
        }

    def _get_soffice_path(self):
        """Tìm đường dẫn thực thi của LibreOffice (soffice)"""
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

    def _convert_to_pdf(self, file_content, extension):
        """Chuyển đổi file gốc sang PDF sử dụng LibreOffice"""
        soffice_path = self._get_soffice_path()
        if not soffice_path:
            _logger.warning("Không tìm thấy LibreOffice để chuyển đổi PDF.")
            return False

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = os.path.join(tmp_dir, f"input.{extension}")
            with open(input_path, 'wb') as f:
                f.write(file_content)
                
            # Nếu là file Excel, điều chỉnh page setup để fit các cột vào 1 trang
            if extension.lower() in ['xlsx', 'xlsm']:
                try:
                    from openpyxl import load_workbook
                    wb = load_workbook(input_path)
                    for ws in wb.worksheets:
                        # Kích hoạt tính năng Fit to Page
                        if ws.sheet_properties.pageSetUpPr:
                            ws.sheet_properties.pageSetUpPr.fitToPage = True
                        else:
                            # Trong trường hợp chưa có thuộc tính, gán lại an toàn
                            from openpyxl.worksheet.properties import PageSetupProperties
                            ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
                        
                        # Cấu hình fit vừa chiều rộng 1 trang (1 trang ngang), để mở chiều cao
                        ws.page_setup.fitToWidth = 1
                        ws.page_setup.fitToHeight = False
                        # Đặt thành khổ giấy ngang để hiển thị được nhiều cột hơn mà không bị quá nhỏ
                        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
                    wb.save(input_path)
                except Exception as e:
                    _logger.warning("Không thể cấu hình fit to page cho file Excel: %s", str(e))
            
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
                _logger.error("Lỗi khi gọi LibreOffice để convert PDF: %s", str(e))
        return False
