# -*- coding: utf-8 -*-
"""Wizard Import/Export Excel cho Bảng giá Ép Film"""
import base64
import io
import openpyxl
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class FilmPricelistExcelWizard(models.TransientModel):
    _name = 'dl.film.pricelist.excel.wizard'
    _description = 'Wizard Nhập/Xuất Excel Bảng giá Ép Film'

    pricelist_id = fields.Many2one('dl.film.pricelist', string='Bảng giá', required=True)
    file_data = fields.Binary(string='File Excel')
    file_name = fields.Char(string='Tên file')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('verified', 'Đã kiểm tra'),
    ], string='Trạng thái', default='draft')
    import_mode = fields.Selection([
        ('update', 'Cập nhật đơn giá (Ghi đè nếu trùng)'),
        ('insert', 'Thêm mới (Chỉ thêm dòng chưa có)'),
    ], string='Chế độ Import', default='update', required=True)
    line_ids = fields.One2many('dl.film.pricelist.excel.line', 'wizard_id', string='Dòng xem trước')

    def action_export(self):
        """Xuất dữ liệu bảng giá Ép Film hiện tại ra Excel"""
        self.ensure_one()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Don_Gia_Ep_Film"

        header_style = openpyxl.styles.Font(bold=True)
        fill = openpyxl.styles.PatternFill(start_color="B8D4E8", end_color="B8D4E8", fill_type="solid")

        headers = ['ID Dòng', 'Tên sản phẩm', 'Thương hiệu Film', 'Số mặt (1m/2m)',
                   'Đơn giá Thường Mới', 'Đơn giá Thường Cũ', 'Đơn giá Sửa Mới', 'Đơn giá Sửa Cũ']
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.font = header_style
            cell.fill = fill

        for row_idx, line in enumerate(self.pricelist_id.line_ids, 2):
            ws.cell(row=row_idx, column=1, value=line.id)
            ws.cell(row=row_idx, column=2, value=line.product_tmpl_id.name)
            ws.cell(row=row_idx, column=3, value=line.x_film_brand_id.name)
            ws.cell(row=row_idx, column=4, value=line.x_surface_type)
            ws.cell(row=row_idx, column=5, value=line.price_high)
            ws.cell(row=row_idx, column=6, value=line.price_low)
            ws.cell(row=row_idx, column=7, value=line.price_re_ep_high)
            ws.cell(row=row_idx, column=8, value=line.price_re_ep_low)

        fp = io.BytesIO()
        wb.save(fp)
        data = base64.b64encode(fp.getvalue())
        fp.close()

        file_name = f"DonGia_EpFilm_{self.pricelist_id.name}.xlsx"
        self.write({'file_data': data, 'file_name': file_name})
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model=dl.film.pricelist.excel.wizard&id={self.id}&field=file_data&download=true&filename={file_name}',
            'target': 'self',
        }

    def action_verify(self):
        """Đọc và kiểm tra file Excel trước khi nhập"""
        self.ensure_one()
        if not self.file_data:
            raise UserError(_("Vui lòng chọn file Excel."))

        try:
            fp = io.BytesIO(base64.b64decode(self.file_data))
            wb = openpyxl.load_workbook(fp, data_only=True)
            ws = wb.active
        except Exception as e:
            raise UserError(_("Lỗi đọc file: %s") % str(e))

        self.line_ids.unlink()
        preview_lines = []
        brand_cache = {}

        for row in ws.iter_rows(min_row=2, values_only=True):
            if not any(row): continue
            line_id = row[0]
            product_name = str(row[1] or '').strip()
            brand_name = str(row[2] or '').strip()
            surface = str(row[3] or '').strip().lower()
            p_high = row[4] or 0.0
            p_low = row[5] or 0.0
            p_re_high = row[6] if len(row) > 6 else 0.0
            p_re_low = row[7] if len(row) > 7 else 0.0

            status = 'ready'
            msgs = []

            if not product_name:
                status = 'error'; msgs.append(_("Thiếu tên sản phẩm"))
            
            # Tìm kiếm sản phẩm
            product_tmpl = self.env['product.template'].search([('name', '=', product_name), ('x_is_wood_product', '=', True)], limit=1)
            if not product_tmpl:
                status = 'error'; msgs.append(_("Không tìm thấy sản phẩm gỗ tên '%s'") % product_name)

            # Kiểm tra Brand
            brand = False
            if brand_name:
                if brand_name in brand_cache:
                    brand = brand_cache[brand_name]
                else:
                    brand = self.env['dl.film.brand'].search([('name', '=', brand_name)], limit=1)
                    brand_cache[brand_name] = brand
            if not brand:
                status = 'error'; msgs.append(_("Không tìm thấy thương hiệu '%s'") % brand_name)

            # Kiểm tra surface
            if surface not in ('1m', '2m'):
                status = 'error'; msgs.append(_("Số mặt '%s' không hợp lệ, chỉ nhận '1m' hoặc '2m'") % surface)

            # Kiểm tra giá
            if any(float(p or 0) < 0 for p in [p_high, p_low, p_re_high, p_re_low]):
                status = 'error'; msgs.append(_("Đơn giá không được âm"))

            preview_lines.append((0, 0, {
                'line_id': int(line_id) if line_id else False,
                'thickness_alias': product_name, # Giữ tên sản phẩm vào field này cho tiện hiển thị
                'brand_name': brand_name,
                'surface_type': surface,
                'price_high': float(p_high or 0),
                'price_low': float(p_low or 0),
                'price_re_ep_high': float(p_re_high or 0),
                'price_re_ep_low': float(p_re_low or 0),
                'status': status,
                'message': ". ".join(msgs) if msgs else _("Hợp lệ"),
            }))

        self.write({'line_ids': preview_lines, 'state': 'verified'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dl.film.pricelist.excel.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_import(self):
        """Nhập các dòng đã được kiểm tra"""
        self.ensure_one()
        if self.state != 'verified':
            return self.action_verify()

        if self.pricelist_id.state == 'confirmed':
            raise UserError(_("Bảng giá đã xác nhận, không thể nhập dữ liệu."))

        valid_lines = self.line_ids.filtered(lambda l: l.status != 'error')
        if not valid_lines:
            raise UserError(_("Không có dòng nào hợp lệ để nhập."))

        success, update, skipped = 0, 0, 0
        for pl in valid_lines:
            brand = self.env['dl.film.brand'].search([('name', '=', pl.brand_name)], limit=1)
            if not brand: continue

            product_tmpl = self.env['product.template'].search([('name', '=', pl.thickness_alias), ('x_is_wood_product', '=', True)], limit=1)
            if not product_tmpl: continue
            
            vals = {
                'pricelist_id': self.pricelist_id.id,
                'product_tmpl_id': product_tmpl.id,
                'x_film_brand_id': brand.id,
                'x_surface_type': pl.surface_type,
                'price_high': pl.price_high,
                'price_low': pl.price_low,
                'price_re_ep_high': pl.price_re_ep_high,
                'price_re_ep_low': pl.price_re_ep_low,
            }

            # Tìm kiếm dòng trùng dựa trên Alias + Brand + Surface
            existing_line = self.env['dl.film.pricelist.line'].search([
                ('pricelist_id', '=', self.pricelist_id.id),
                ('product_tmpl_id', '=', product_tmpl.id),
                ('x_film_brand_id', '=', brand.id),
                ('x_surface_type', '=', pl.surface_type),
            ], limit=1)

            if existing_line:
                if self.import_mode == 'update':
                    existing_line.write(vals)
                    update += 1
                else:
                    skipped += 1
            else:
                self.env['dl.film.pricelist.line'].create(vals)
                success += 1

        msg = _('Kết quả: Tạo mới %d, Cập nhật %d') % (success, update)
        if skipped:
            msg += _(', Bỏ qua %d dòng trùng') % skipped
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Nhập dữ liệu hoàn tất'),
                'message': msg,
                'type': 'success' if (success + update) > 0 else 'warning',
            }
        }


class FilmPricelistExcelLine(models.TransientModel):
    _name = 'dl.film.pricelist.excel.line'
    _description = 'Dòng xem trước Excel Ép Film'

    wizard_id = fields.Many2one('dl.film.pricelist.excel.wizard', ondelete='cascade')
    line_id = fields.Integer(string='ID Dòng Gốc')
    thickness_alias = fields.Char(string='Ký hiệu độ dày')
    brand_name = fields.Char(string='Thương hiệu Film')
    surface_type = fields.Char(string='Số mặt')
    price_high = fields.Float(string='Đơn giá Thường Mới')
    price_low = fields.Float(string='Đơn giá Thường Cũ')
    price_re_ep_high = fields.Float(string='Đơn giá Sửa Mới')
    price_re_ep_low = fields.Float(string='Đơn giá Sửa Cũ')
    status = fields.Selection([
        ('ready', 'Hợp lệ'), ('warning', 'Cảnh báo'), ('error', 'Lỗi')
    ], string='Trạng thái', default='ready')
    message = fields.Text(string='Thông báo')
