# -*- coding: utf-8 -*-
import base64
import xlrd
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class DlWoodPeelingDossierImportWizard(models.TransientModel):
    _name = 'dl.wood.peeling.dossier.import.wizard'
    _description = 'Import Hồ Sơ Ván Bóc'

    file = fields.Binary(string='File Excel', required=True)
    file_name = fields.Char(string='Tên file')

    def action_import(self):
        self.ensure_one()
        if not self.file:
            raise UserError(_("Vui lòng tải lên file Excel."))
            
        file_data = base64.b64decode(self.file)
        try:
            workbook = xlrd.open_workbook(file_contents=file_data)
            sheet = workbook.sheet_by_index(0)
        except Exception as e:
            raise UserError(_("File không đúng định dạng Excel. Chi tiết lỗi: %s") % str(e))

        dossier_env = self.env['dl.wood.peeling.dossier']
        partner_env = self.env['res.partner']
        
        imported_count = 0
        error_rows = []

        # Bắt đầu đọc từ dòng thứ 2 (bỏ qua header)
        for row_idx in range(1, sheet.nrows):
            try:
                row = sheet.row_values(row_idx)
                if not row or not any(row):
                    continue

                # Mapping cột:
                # 0: NCC Ván Bóc (Tên) *
                # 1: Tên Hồ Sơ
                # 2: Tên Chủ Rừng
                # 3: CCCD Chủ Rừng
                # 4: Địa chỉ Chủ Rừng
                # 5: SĐT Chủ Rừng
                # 6: Địa danh khai thác
                # 7: Diện tích (ha)
                
                partner_name = str(row[0]).strip() if len(row) > 0 else ''
                if not partner_name:
                    error_rows.append(f"Dòng {row_idx + 1}: Thiếu tên Nhà Cung Cấp.")
                    continue
                    
                # Tìm NCC
                partner = partner_env.search([('name', '=', partner_name), ('x_is_peeling_supplier', '=', True)], limit=1)
                if not partner:
                    error_rows.append(f"Dòng {row_idx + 1}: Không tìm thấy NCC '{partner_name}'.")
                    continue

                dossier_name = str(row[1]).strip() if len(row) > 1 else ''
                forest_owner = str(row[2]).strip() if len(row) > 2 else ''
                
                # Format CCCD thành chuỗi số
                cccd = row[3] if len(row) > 3 else ''
                if isinstance(cccd, float):
                    cccd = str(int(cccd))
                else:
                    cccd = str(cccd).strip()
                    
                owner_addr = str(row[4]).strip() if len(row) > 4 else ''
                
                # Format SĐT
                phone = row[5] if len(row) > 5 else ''
                if isinstance(phone, float):
                    phone = str(int(phone))
                else:
                    phone = str(phone).strip()
                    
                expl_addr = str(row[6]).strip() if len(row) > 6 else ''
                
                # Diện tích
                area_val = row[7] if len(row) > 7 else 0.0
                try:
                    area = float(area_val) if area_val else 0.0
                except ValueError:
                    area = 0.0

                vals = {
                    'partner_id': partner.id,
                    'x_dossier_name': dossier_name,
                    'x_forest_owner_name': forest_owner,
                    'x_forest_owner_cccd': cccd,
                    'x_forest_owner_address': owner_addr,
                    'x_forest_owner_phone': phone,
                    'x_exploitation_address': expl_addr,
                    'x_exploitation_area': area,
                }
                
                dossier_env.create(vals)
                imported_count += 1
                
            except Exception as e:
                error_rows.append(f"Dòng {row_idx + 1}: Lỗi không xác định - {str(e)}")

        msg = f"Đã import thành công {imported_count} hồ sơ."
        if error_rows:
            msg += "\n\nCác lỗi xảy ra:\n" + "\n".join(error_rows)
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Kết quả Import'),
                'message': msg,
                'type': 'success' if imported_count > 0 else 'danger',
                'sticky': bool(error_rows),
            }
        }


class DlWoodPeelingInvoiceImportPreviewLine(models.TransientModel):
    _name = 'dl.wood.peeling.invoice.import.preview.line'
    _description = 'Dòng xem trước Import Hoá Đơn'

    wizard_id = fields.Many2one('dl.wood.peeling.invoice.import.wizard', ondelete='cascade')
    row_number = fields.Integer(string='Dòng')
    dossier_name = fields.Char(string='Mã Hồ Sơ')
    partner_name = fields.Char(string='Nhà Cung Cấp')
    forest_owner_name = fields.Char(string='Chủ Rừng')
    invoice_number = fields.Char(string='Số Hoá Đơn')
    invoice_date = fields.Date(string='Ngày Hoá Đơn')
    qty_initial = fields.Float(string='Khối lượng')
    price_unit = fields.Float(string='Đơn giá')
    subtotal = fields.Float(string='Thành tiền')
    bkls_number = fields.Char(string='Số BKLS')
    error_message = fields.Char(string='Lỗi')
    is_valid = fields.Boolean(string='Hợp lệ', default=True)


class DlWoodPeelingInvoiceImportWizard(models.TransientModel):
    _name = 'dl.wood.peeling.invoice.import.wizard'
    _description = 'Import Hoá Đơn Ván Bóc'

    state = fields.Selection([
        ('upload', 'Tải lên'),
        ('preview', 'Xem trước')
    ], string='Trạng thái', default='upload')
    
    file = fields.Binary(string='File Excel')
    file_name = fields.Char(string='Tên file')
    dossier_id = fields.Many2one('dl.wood.peeling.dossier', string='Hồ Sơ Ván Bóc', readonly=True)
    template_file = fields.Binary(string='File Mẫu')
    template_filename = fields.Char(string='Tên File Mẫu')
    
    preview_line_ids = fields.One2many('dl.wood.peeling.invoice.import.preview.line', 'wizard_id', string='Dữ liệu xem trước')
    total_rows = fields.Integer(string='Tổng số dòng', default=0)
    error_rows = fields.Integer(string='Số dòng lỗi', default=0)

    def action_download_template(self):
        import base64
        import io
        try:
            import xlsxwriter
        except ImportError:
            raise UserError(_("Thư viện xlsxwriter chưa được cài đặt. Vui lòng cài đặt để sử dụng tính năng này."))
            
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Template')
        
        text_format = workbook.add_format({'num_format': '@'})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        
        headers = ['Mã Hồ Sơ VB', 'Số Hoá Đơn', 'Ngày Hoá Đơn (dd/mm/yyyy)', 'Khối Lượng (m3)', 'Đơn Giá', 'Số BKLS']
        for col, h in enumerate(headers):
            worksheet.write(0, col, h)
            
        # Format cột Số Hoá Đơn (cột B) thành Text để giữ nguyên số 0 ở đầu
        worksheet.set_column(1, 1, 15, text_format)
        # Format cột Ngày Hoá Đơn (cột C) thành chuẩn Date của VN
        worksheet.set_column(2, 2, 25, date_format)
            
        if self.dossier_id:
            worksheet.write(1, 0, self.dossier_id.name)
            worksheet.write(1, 1, '000123', text_format)
            
        workbook.close()
        output.seek(0)
        file_data = base64.b64encode(output.read())
        
        self.write({
            'template_file': file_data,
            'template_filename': 'Template_Import_Hoa_Don.xlsx'
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model=dl.wood.peeling.invoice.import.wizard&id={self.id}&field=template_file&download=true&filename={self.template_filename}',
            'target': 'self'
        }

    def action_preview(self):
        self.ensure_one()
        if not self.file:
            raise UserError(_("Vui lòng tải lên file Excel."))
            
        file_data = base64.b64decode(self.file)
        try:
            workbook = xlrd.open_workbook(file_contents=file_data)
            sheet = workbook.sheet_by_index(0)
        except Exception as e:
            raise UserError(_("File không đúng định dạng Excel. Chi tiết lỗi: %s") % str(e))

        dossier_env = self.env['dl.wood.peeling.dossier']
        
        # Xoá preview cũ
        self.preview_line_ids.unlink()
        
        preview_vals = []
        for row_idx in range(1, sheet.nrows):
            try:
                row = sheet.row_values(row_idx)
                if not row or not any(row):
                    continue

                error_msgs = []
                is_valid = True

                if self.dossier_id:
                    dossier = self.dossier_id
                    dossier_name = self.dossier_id.name
                else:
                    dossier_name = str(row[0]).strip() if len(row) > 0 else ''
                    if not dossier_name:
                        error_msgs.append("Thiếu Mã Hồ Sơ VB")
                        is_valid = False
                        dossier = None
                    else:
                        dossier = dossier_env.search([('name', '=', dossier_name)], limit=1)
                        if not dossier:
                            error_msgs.append(f"Không tìm thấy Hồ sơ '{dossier_name}'")
                            is_valid = False

                inv_num_raw = row[1] if len(row) > 1 else ''
                if isinstance(inv_num_raw, float):
                    inv_num = str(int(inv_num_raw))
                else:
                    inv_num = str(inv_num_raw).strip()
                    
                if not inv_num:
                    error_msgs.append("Thiếu Số Hoá Đơn")
                    is_valid = False
                    
                inv_date_val = row[2] if len(row) > 2 else ''
                inv_date = False
                if inv_date_val:
                    if isinstance(inv_date_val, float):
                        try:
                            dt_tuple = xlrd.xldate_as_tuple(inv_date_val, workbook.datemode)
                            inv_date = f"{dt_tuple[0]:04d}-{dt_tuple[1]:02d}-{dt_tuple[2]:02d}"
                        except:
                            error_msgs.append("Ngày hoá đơn lỗi định dạng")
                            is_valid = False
                    else:
                        try:
                            parts = str(inv_date_val).strip().split('/')
                            if len(parts) == 3:
                                inv_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
                        except:
                            error_msgs.append("Ngày hoá đơn lỗi định dạng")
                            is_valid = False
                            
                if not inv_date:
                    inv_date = fields.Date.context_today(self)

                qty_val = row[3] if len(row) > 3 else 0.0
                try:
                    qty = float(qty_val) if qty_val else 0.0
                except ValueError:
                    qty = 0.0
                    error_msgs.append("Khối lượng không hợp lệ")
                    is_valid = False
                    
                if qty <= 0:
                    error_msgs.append("Khối lượng phải > 0")
                    is_valid = False

                price_val = row[4] if len(row) > 4 else 0.0
                try:
                    price = float(price_val) if price_val else 0.0
                except ValueError:
                    price = 0.0
                    
                bkls_num_raw = row[5] if len(row) > 5 else ''
                if isinstance(bkls_num_raw, float):
                    bkls_num = str(int(bkls_num_raw))
                else:
                    bkls_num = str(bkls_num_raw).strip()

                partner_name = dossier.partner_id.name if dossier and dossier.partner_id else ''
                forest_owner_name = dossier.x_forest_owner_name if dossier else ''

                preview_vals.append((0, 0, {
                    'row_number': row_idx + 1,
                    'dossier_name': dossier_name,
                    'partner_name': partner_name,
                    'forest_owner_name': forest_owner_name,
                    'invoice_number': inv_num,
                    'invoice_date': inv_date,
                    'qty_initial': qty,
                    'price_unit': price,
                    'subtotal': qty * price,
                    'bkls_number': bkls_num,
                    'error_message': " | ".join(error_msgs) if error_msgs else "",
                    'is_valid': is_valid
                }))
                
            except Exception as e:
                preview_vals.append((0, 0, {
                    'row_number': row_idx + 1,
                    'error_message': f"Lỗi không xác định: {str(e)}",
                    'is_valid': False
                }))

        total_rows = len(preview_vals)
        error_rows = sum(1 for p in preview_vals if not p[2].get('is_valid'))
        
        self.write({
            'preview_line_ids': preview_vals,
            'total_rows': total_rows,
            'error_rows': error_rows,
            'state': 'preview'
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dl.wood.peeling.invoice.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_back_to_upload(self):
        self.write({'state': 'upload'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dl.wood.peeling.invoice.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_import(self):
        self.ensure_one()
        invoice_env = self.env['dl.wood.peeling.invoice']
        dossier_env = self.env['dl.wood.peeling.dossier']
        
        valid_lines = self.preview_line_ids.filtered(lambda l: l.is_valid)
        if not valid_lines:
            raise UserError(_("Không có dữ liệu hợp lệ nào để import!"))
            
        imported_count = 0
        for line in valid_lines:
            if self.dossier_id:
                dossier = self.dossier_id
            else:
                dossier = dossier_env.search([('name', '=', line.dossier_name)], limit=1)
                
            if not dossier:
                continue

            vals = {
                'dossier_id': dossier.id,
                'invoice_number': line.invoice_number,
                'invoice_date': line.invoice_date,
                'qty_initial': line.qty_initial,
                'price_unit': line.price_unit,
                'bkls_number': line.bkls_number,
            }
            invoice_env.create(vals)
            imported_count += 1
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Kết quả Import'),
                'message': f"Đã import thành công {imported_count} hoá đơn.",
                'type': 'success',
                'sticky': False,
            }
        }
