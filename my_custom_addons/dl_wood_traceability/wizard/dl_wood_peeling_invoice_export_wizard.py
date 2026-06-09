# -*- coding: utf-8 -*-
import base64
import io
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

class DlWoodPeelingInvoiceExportWizard(models.TransientModel):
    _name = 'dl.wood.peeling.invoice.export.wizard'
    _description = 'Wizard Xuất Excel Hoá Đơn Ván Bóc'

    date_from = fields.Date(string='Từ ngày')
    date_to = fields.Date(string='Đến ngày')
    state = fields.Selection([
        ('all', 'Tất cả'),
        ('available', 'Còn hàng'),
        ('partial', 'Đã dùng 1 phần'),
        ('depleted', 'Đã hết')
    ], string='Trạng thái', default='all', required=True)

    def action_export(self):
        self.ensure_one()
        
        if not xlsxwriter:
            raise UserError(_("Thiếu thư viện xlsxwriter, vui lòng cài đặt bằng lệnh: pip install xlsxwriter"))
        
        # Build domain
        domain = []
        if self.date_from:
            domain.append(('invoice_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('invoice_date', '<=', self.date_to))
        if self.state != 'all':
            domain.append(('state', '=', self.state))
            
        invoices = self.env['dl.wood.peeling.invoice'].search(domain, order='invoice_date desc, id desc')
        
        if not invoices:
            raise UserError(_("Không có dữ liệu hoá đơn ván bóc nào phù hợp với bộ lọc!"))
            
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Hoá đơn ván bóc')
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#D9E1F2',
            'border': 1
        })
        cell_format = workbook.add_format({'border': 1, 'valign': 'vcenter'})
        num_format = workbook.add_format({'border': 1, 'valign': 'vcenter', 'num_format': '#,##0.000'})
        currency_format = workbook.add_format({'border': 1, 'valign': 'vcenter', 'num_format': '#,##0'})
        date_format = workbook.add_format({'border': 1, 'valign': 'vcenter', 'num_format': 'dd/mm/yyyy'})
        
        # Headers
        headers = [
            'STT', 'Số Hóa Đơn', 'Ngày HĐ', 'Mã Hồ Sơ', 'Nhà Cung Cấp', 
            'Bảng kê lâm sản', 'Loại ván bóc', 'Loại gỗ', 
            'KL ban đầu (m³)', 'KL đã dùng (m³)', 'Tồn khả dụng (m³)', 
            'Tổng tiền (VNĐ)', 'Trạng thái'
        ]
        
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)
            
        # Set column widths
        worksheet.set_column(0, 0, 5)   # STT
        worksheet.set_column(1, 1, 15)  # Số HĐ
        worksheet.set_column(2, 2, 12)  # Ngày HĐ
        worksheet.set_column(3, 3, 20)  # Mã Hồ sơ
        worksheet.set_column(4, 4, 30)  # NCC
        worksheet.set_column(5, 5, 25)  # BKLS
        worksheet.set_column(6, 6, 25)  # Loại ván bóc
        worksheet.set_column(7, 7, 20)  # Loại gỗ
        worksheet.set_column(8, 10, 15) # Khối lượng
        worksheet.set_column(11, 11, 20) # Tổng tiền
        worksheet.set_column(12, 12, 15) # Trạng thái
        
        row = 1
        for idx, inv in enumerate(invoices):
            state_str = ''
            if inv.state == 'available': state_str = 'Còn hàng'
            elif inv.state == 'partial': state_str = 'Đã dùng 1 phần'
            elif inv.state == 'depleted': state_str = 'Đã hết'
            
            # Formatting fields
            dossier_code = inv.dossier_id.name if inv.dossier_id else ''
            partner_name = inv.partner_id.name if inv.partner_id else ''
            bkls_nums = ', '.join(inv.bkls_ids.mapped('bkls_number'))
            
            # Gather unique variants and species
            variants = inv.bkls_ids.mapped('line_ids.peeling_variant_id.name')
            species = inv.bkls_ids.mapped('line_ids.peeling_variant_id.peeling_type_id.species_id.name')
            variant_str = ', '.join(set([v for v in variants if v]))
            species_str = ', '.join(set([s for s in species if s]))
            
            worksheet.write(row, 0, idx + 1, cell_format)
            worksheet.write(row, 1, inv.invoice_number or inv.name or '', cell_format)
            if inv.invoice_date:
                worksheet.write_datetime(row, 2, inv.invoice_date, date_format)
            else:
                worksheet.write(row, 2, '', cell_format)
            worksheet.write(row, 3, dossier_code, cell_format)
            worksheet.write(row, 4, partner_name, cell_format)
            worksheet.write(row, 5, bkls_nums, cell_format)
            worksheet.write(row, 6, variant_str, cell_format)
            worksheet.write(row, 7, species_str, cell_format)
            
            worksheet.write_number(row, 8, inv.qty_initial or 0.0, num_format)
            worksheet.write_number(row, 9, inv.qty_used or 0.0, num_format)
            worksheet.write_number(row, 10, inv.qty_available or 0.0, num_format)
            worksheet.write_number(row, 11, inv.x_subtotal or 0.0, currency_format)
            worksheet.write(row, 12, state_str, cell_format)
            
            row += 1
            
        workbook.close()
        output.seek(0)
        
        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': f'Danh_sach_HD_Van_Boc_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
