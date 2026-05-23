# -*- coding: utf-8 -*-
"""
dl.wood.dossier - Hồ Sơ Gỗ (Master Data)
"""
from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError
import logging
import io
import base64
import os
import re
import zipfile
import traceback

# Import renderer và helper functions từ file riêng biệt
from .dl_wood_dossier_renderer import (
    DossierDocxRenderer,
    date_to_vietnamese_text,
    no_accent_vietnamese,
)

_logger = logging.getLogger(__name__)


class DlWoodPdfMixin(models.AbstractModel):
    _name = 'dl.wood.pdf.mixin'
    _description = 'Hỗ trợ chuyển đổi PDF'

    def _get_soffice_path(self):
        """Tìm đường dẫn thực thi của LibreOffice (soffice)"""
        import shutil
        import os
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

    def _convert_docx_to_pdf(self, docx_content):
        """Chuyển đổi DOCX sang PDF sử dụng LibreOffice"""
        import subprocess
        import tempfile
        import os

        soffice_path = self._get_soffice_path()
        if not soffice_path:
            raise UserError(_("Không tìm thấy LibreOffice (soffice) trên máy chủ để chuyển đổi PDF."))

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = os.path.join(tmp_dir, "input.docx")
            with open(input_path, 'wb') as f:
                f.write(docx_content)
            
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
                _logger.error("Lỗi khi gọi LibreOffice: %s", str(e))
                raise UserError(_("Lỗi trong quá trình chuyển đổi PDF: %s") % str(e))
        return None




class DlWoodDossier(models.Model):
    _name = 'dl.wood.dossier'
    _description = 'Hồ Sơ Gỗ (Nguồn khai thác)'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'dl.wood.log.mixin', 'dl.wood.pdf.mixin']
    _order = 'id desc'

    @api.depends('name', 'partner_id.name', 'qty_available')
    def _compute_display_name(self):
        for dossier in self:
            if self.env.context.get('dossier_show_code_only'):
                dossier.display_name = dossier.name or ""
            else:
                partner_name = dossier.partner_id.name or 'Không có chủ rừng'
                qty_avail = dossier.qty_available or 0.0
                dossier.display_name = f"{dossier.name} - {partner_name} - {qty_avail:.2f} m³"

    @api.model
    def _get_default_name(self):
        prefix = self.env.company.x_wood_prefix or "XX"
        # Đếm số lượng hồ sơ hiện có của công ty để cộng thêm 1
        count = self.search_count([('company_id', '=', self.env.company.id)])
        return f"{prefix}_HS_{(count + 1):04d}"

    name = fields.Char(string='Mã Hồ Sơ', required=True, copy=False, readonly=True, default=_get_default_name)
    x_dossier_name = fields.Char(string='Tên Hồ Sơ', help='Tên mô tả ngắn gọn cho bộ hồ sơ')
    partner_id = fields.Many2one(
        'res.partner', 
        string='Chủ Rừng / Nhà Cung Cấp', 
        required=True, 
        domain="[('active', '=', True), ('x_is_wood_supplier', '!=', False), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        check_company=True
    )
    x_prep_days = fields.Integer(
        string='Thời gian chuẩn bị (ngày)',
        help='Thời gian chuẩn bị của bộ hồ sơ này. Mặc định lấy từ Chủ rừng.'
    )
    x_exploitation_capacity = fields.Integer(
        string='Năng lực khai thác (m³/ngày)',
        help='Năng lực khai thác của bộ hồ sơ này. Mặc định lấy từ Chủ rừng.'
    )
    x_transport_method = fields.Selection([
        ('urgent', 'Gấp'),
        ('normal', 'Bình thường'),
        ('slow', 'Từ từ')
    ], string='Cách vận chuyển', default='normal', required=True,
       help="• Gấp: mỗi xe chạy 2 chuyến/ngày\n"
            "• Bình thường: mỗi xe 1 chuyến/ngày\n"
            "• Từ từ: 2 ngày/chuyến/xe")
    partner_address = fields.Char(string='Địa chỉ', compute='_compute_partner_address', store=True, readonly=True)
    
    # Thông tin lâm nghiệp
    exploitation_location_id = fields.Many2one('dl.wood.exploitation.location', string='Địa bàn khai thác')
    x_mining_address = fields.Char(string='Địa chỉ khai thác (WoodPro)')
    x_area = fields.Float(string='Diện tích (ha)', digits=(16, 2))
    x_mining_method = fields.Selection([
        ('white', 'Khai thác trắng'),
        ('group', 'Khai thác theo đám')
    ], string='Phương thức khai thác', default='white')
    
    def _default_x_report_version_id(self):
        version = self.env['dl.wood.report.version'].search([
            ('active', '=', True)
        ], order='id desc', limit=1)
        return version.id if version else False

    date_received = fields.Date(string='Ngày nhận hồ sơ', default=fields.Date.context_today)
    x_start_date = fields.Date(string='Khai thác từ', help='Ngày bắt đầu khai thác gỗ thực tế tại rừng.')
    x_end_date = fields.Date(string='Khai thác đến', help='Tự động tính: [Khai thác từ] + [Thời gian khai thác cần thiết]. Trong đó, thời gian khai thác tính tự động dựa trên tổng diện tích (ha) của địa bàn.')
    x_report_version_id = fields.Many2one(
        'dl.wood.report.version', 
        string='Phiên bản biểu mẫu', 
        ondelete='restrict',
        default=_default_x_report_version_id
    )
    x_exploitation_period_text = fields.Char(string='Thời gian khai thác (Văn bản)', compute='_compute_exploitation_period_text', store=False)
    x_addendum_num = fields.Char(string='Số phụ lục', compute='_compute_addendum_num', store=True, readonly=False)
    x_bkls_number = fields.Char(string='Mã số Bảng kê lâm sản', compute='_compute_x_bkls_number', store=True, readonly=False)
    x_contract_number = fields.Char(
        string='Số hợp đồng',
        compute='_compute_contract_number',
        store=True,
        readonly=False,
        help='Tự động tính: [NgàyTháng]/[Năm]/HD-[Tiền tố]-[Viết tắt chủ rừng]'
    )

    # Thông tin Hợp đồng
    x_contract_date = fields.Date(
        string='Ngày ký hợp đồng',
        compute='_compute_contract_date_default',
        store=True,
        readonly=False,
        help='Tự động tính: [Khai thác đến] + 1 ngày (nếu vào Chủ Nhật sẽ tự động +1 ngày để sang Thứ Hai). Hợp đồng được ký ngay sau khi kết thúc khai thác để đảm bảo kiểm đếm số liệu gỗ chính xác.'
    )
    x_owner_representative = fields.Char(string='Đại diện chủ rừng')
    x_owner_position = fields.Char(string='Chức vụ đại diện chủ rừng', default='Chủ rừng')
    
    # 3 trường ngày mới liên kết đồng bộ
    x_addendum_date = fields.Date(
        string='Ngày lập phụ lục',
        compute='_compute_paper_dates',
        store=True,
        readonly=False,
        help='Mặc định tự động lấy bằng Ngày ký hợp đồng.'
    )
    x_bkls_date = fields.Date(
        string='Ngày lập bảng kê lâm sản',
        compute='_compute_paper_dates',
        store=True,
        readonly=False,
        help='Mặc định tự động lấy bằng Ngày ký hợp đồng.'
    )
    x_verify_date = fields.Date(
        string='Ngày Kiểm lâm xác nhận',
        compute='_compute_paper_dates',
        store=True,
        readonly=False,
        help='Mặc định tự động lấy bằng Ngày ký hợp đồng.'
    )
    
    # Đại diện Công ty (thay cho Lập Phương án PAKT)
    x_company_representative = fields.Char(string='Đại diện công ty', compute='_compute_company_rep_info', store=True, readonly=False)
    x_company_position = fields.Char(string='Chức vụ đại diện công ty', compute='_compute_company_rep_info', store=True, readonly=False)
    
    # Mốc thời gian vận chuyển / giao hàng
    x_delivery_start_date = fields.Date(
        string='Giao hàng từ',
        compute='_compute_delivery_dates',
        store=True,
        readonly=False,
        help='Tự động tính: [Ngày khai thác đến] + trễ từ 2 đến 5 ngày tùy theo khối lượng gỗ (Nếu trùng Chủ Nhật sẽ tự động cộng 1 ngày để sang Thứ Hai).'
    )
    x_delivery_end_date = fields.Date(
        string='Giao hàng đến',
        compute='_compute_delivery_dates',
        store=True,
        readonly=False,
        help='Tự động tính: Mỗi ngày vận chuyển 1 chuyến xe (dựa theo số chuyến thực tế hoặc ước tính), tự động bỏ qua các ngày Chủ Nhật.'
    )
    x_delivery_explanation = fields.Html(
        string='Giải thích lịch giao hàng',
        compute='_compute_delivery_explanation'
    )

    @api.depends('x_end_date', 'initial_wood_qty', 'initial_firewood_qty', 'ticket_ids', 'transport_ids', 'x_delivery_start_date', 'x_delivery_end_date', 'x_transport_method')
    def _compute_delivery_explanation(self):
        import math
        from datetime import timedelta
        for record in self:
            if not record.x_end_date or not record.x_delivery_start_date or not record.x_delivery_end_date:
                record.x_delivery_explanation = False
                continue

            # 1. Xác định delay dựa trên tổng gỗ + củi (Ster ~ m3 xếp đống)
            volume = (record.initial_wood_qty or 0.0) + (record.initial_firewood_qty or 0.0)
            if volume <= 100:
                delay = 2
            elif volume <= 300:
                delay = 3
            elif volume <= 600:
                delay = 4
            else:
                delay = 5

            # Tính ngày bắt đầu thô và kiểm tra xem có trùng Chủ Nhật không
            raw_start_date = record.x_end_date + timedelta(days=delay)
            was_sunday = (raw_start_date.weekday() == 6)

            # 2. Xác định số chuyến xe
            trips_count = len(record.ticket_ids)
            if trips_count == 0:
                if record.transport_ids:
                    first_transport = record.transport_ids[0]
                    capacity = first_transport.vehicle_id.capacity or 1.0
                    if capacity > 0:
                        trips_wood = math.ceil(record.initial_wood_qty / (capacity * 0.98)) if record.initial_wood_qty > 0 else 0
                        trips_firewood = math.ceil(record.initial_firewood_qty / (capacity * 0.98)) if record.initial_firewood_qty > 0 else 0
                        trips_count = trips_wood + trips_firewood
                if trips_count == 0:
                    trips_count = 1

            # 3. Đếm số ngày Chủ Nhật bị loại trừ trong khoảng giao hàng dựa theo chế độ vận chuyển (x_transport_method)
            # urgent: 2 chuyến/ngày
            # normal: 1 chuyến/ngày
            # slow: 2 ngày mới có 1 chuyến (giao vào các ngày làm việc lẻ)
            sundays = []
            current_date = record.x_delivery_start_date
            trips_delivered = 0
            
            if record.x_transport_method == 'urgent':
                trips_delivered = min(2, trips_count)
            elif record.x_transport_method == 'slow':
                trips_delivered = min(1, trips_count)
                work_day_index = 1
            else: # normal
                trips_delivered = min(1, trips_count)

            while trips_delivered < trips_count:
                current_date += timedelta(days=1)
                if current_date.weekday() == 6:
                    sundays.append(current_date.strftime('%d/%m/%Y'))
                else:
                    if record.x_transport_method == 'urgent':
                        trips_delivered += 2
                    elif record.x_transport_method == 'slow':
                        work_day_index += 1
                        if work_day_index % 2 == 1:
                            trips_delivered += 1
                    else: # normal
                        trips_delivered += 1

            # 4. Tạo chuỗi giải thích tiếng Việt cực kỳ chi tiết
            end_date_str = record.x_end_date.strftime('%d/%m/%Y')
            start_date_str = record.x_delivery_start_date.strftime('%d/%m/%Y')
            delivery_end_str = record.x_delivery_end_date.strftime('%d/%m/%Y')
            
            # Tiêu đề khoảng khối lượng để in ra giải thích
            if volume <= 100:
                vol_range_str = "nhỏ (&le; 100 m³/Ster)"
            elif volume <= 300:
                vol_range_str = "trung bình (101 - 300 m³/Ster)"
            elif volume <= 600:
                vol_range_str = "khá lớn (301 - 600 m³/Ster)"
            else:
                vol_range_str = "rất lớn (&gt; 600 m³/Ster)"
            
            if record.x_transport_method == 'urgent':
                freq_str = "tần suất mỗi ngày chở 2 chuyến"
            elif record.x_transport_method == 'slow':
                freq_str = "tần suất 2 ngày chở 1 chuyến"
            else:
                freq_str = "tần suất mỗi ngày chở 1 chuyến"
            
            explanation = f"""
            <div class="text-muted alert alert-info mt-2 mb-0 border-0 p-2" style="font-size: 0.85em; background-color: #f0f8ff;" role="status">
                <i class="fa fa-info-circle text-info mr-1" title="Chi tiết tính toán"></i>
                <strong>Chi tiết cách tính lịch giao hàng:</strong><br/>
                • Ngày khai thác đến là <strong>{end_date_str}</strong>.<br/>
                • Do tổng khối lượng lâm sản là <strong>{volume:,.2f} m³/Ster</strong> (Gỗ: {record.initial_wood_qty:,.2f} m³, Củi: {record.initial_firewood_qty:,.2f} Ster) thuộc khoảng {vol_range_str}, hệ thống tự động áp dụng thời gian trễ là <strong>{delay} ngày</strong>.
            """
            
            if was_sunday:
                raw_start_str = raw_start_date.strftime('%d/%m/%Y')
                explanation += f" Ngày bắt đầu dự tính là <em>{raw_start_str} (Chủ Nhật)</em> nên tự động lùi 1 ngày sang Thứ Hai ngày <strong>{start_date_str}</strong>.<br/>"
            else:
                explanation += f" Ngày bắt đầu giao hàng thực tế là ngày <strong>{start_date_str}</strong>.<br/>"

            explanation += f"• Tổng cộng có <strong>{trips_count} chuyến xe</strong> vận chuyển ({freq_str}).<br/>"
            
            if sundays:
                sundays_str = ", ".join(sundays)
                explanation += f"• Hệ thống tự động phát hiện và <strong>loại trừ {len(sundays)} ngày Chủ Nhật</strong> ({sundays_str}) nghỉ làm việc.<br/>"
            else:
                explanation += "• Lịch trình giao hàng liên tục không trải qua ngày Chủ Nhật nào.<br/>"

            explanation += f"• Vì vậy, ngày kết thúc giao hàng chính xác là <strong>{delivery_end_str}</strong>."
            explanation += "</div>"
            
            record.x_delivery_explanation = explanation

    @api.depends('x_end_date', 'initial_wood_qty', 'initial_firewood_qty', 'ticket_ids', 'transport_ids', 'x_transport_method')
    def _compute_delivery_dates(self):
        import math
        from datetime import timedelta
        for record in self:
            if not record.x_end_date:
                record.x_delivery_start_date = False
                record.x_delivery_end_date = False
                continue

            # 1. Tính ngày bắt đầu giao hàng (Khai thác đến + delay từ 2 đến 5 ngày dựa theo khối lượng)
            volume = (record.initial_wood_qty or 0.0) + (record.initial_firewood_qty or 0.0)
            if volume <= 100:
                delay = 2
            elif volume <= 300:
                delay = 3
            elif volume <= 600:
                delay = 4
            else:
                delay = 5
                
            start_date = record.x_end_date + timedelta(days=delay)
            if start_date.weekday() == 6:  # Nếu là Chủ Nhật
                start_date += timedelta(days=1)  # Chuyển sang thứ 2
            record.x_delivery_start_date = start_date

            # 2. Tính số chuyến (số tickets hoặc ước lượng)
            trips_count = len(record.ticket_ids)
            if trips_count == 0:
                if record.transport_ids:
                    first_transport = record.transport_ids[0]
                    capacity = first_transport.vehicle_id.capacity or 1.0
                    if capacity > 0:
                        trips_wood = math.ceil(record.initial_wood_qty / (capacity * 0.98)) if record.initial_wood_qty > 0 else 0
                        trips_firewood = math.ceil(record.initial_firewood_qty / (capacity * 0.98)) if record.initial_firewood_qty > 0 else 0
                        trips_count = trips_wood + trips_firewood
                if trips_count == 0:
                    trips_count = 1

            # 3. Tính ngày kết thúc giao hàng dựa theo chế độ vận chuyển (x_transport_method)
            # urgent: 2 chuyến/ngày
            # normal: 1 chuyến/ngày
            # slow: 2 ngày mới có 1 chuyến
            current_date = start_date
            trips_delivered = 0
            
            if record.x_transport_method == 'urgent':
                trips_delivered = min(2, trips_count)
            elif record.x_transport_method == 'slow':
                trips_delivered = min(1, trips_count)
                work_day_index = 1
            else: # normal
                trips_delivered = min(1, trips_count)

            while trips_delivered < trips_count:
                current_date += timedelta(days=1)
                if current_date.weekday() != 6: # Ngày làm việc (khác Chủ Nhật)
                    if record.x_transport_method == 'urgent':
                        trips_delivered += 2
                    elif record.x_transport_method == 'slow':
                        work_day_index += 1
                        if work_day_index % 2 == 1:
                            trips_delivered += 1
                    else: # normal
                        trips_delivered += 1
                        
            record.x_delivery_end_date = current_date

    @api.depends('company_id')
    def _compute_company_rep_info(self):
        for record in self:
            if record.company_id:
                if not record.x_company_representative:
                    record.x_company_representative = getattr(record.company_id, 'x_representative', '') or ''
                if not record.x_company_position:
                    record.x_company_position = 'Giám đốc'
            else:
                if not record.x_company_representative:
                    record.x_company_representative = ''
                if not record.x_company_position:
                    record.x_company_position = 'Giám đốc'

    @api.depends('x_end_date')
    def _compute_contract_date_default(self):
        from datetime import timedelta
        for record in self:
            if record.x_end_date:
                record.x_contract_date = record.x_end_date + timedelta(days=1)
            else:
                record.x_contract_date = False

    @api.depends('x_contract_date')
    def _compute_paper_dates(self):
        for record in self:
            if record.x_contract_date:
                record.x_addendum_date = record.x_contract_date
                record.x_bkls_date = record.x_contract_date
                record.x_verify_date = record.x_contract_date
            else:
                record.x_addendum_date = False
                record.x_bkls_date = False
                record.x_verify_date = False

    @api.depends('x_start_date', 'x_end_date')
    def _compute_exploitation_period_text(self):
        for record in self:
            if record.x_start_date and record.x_end_date:
                start_str = record.x_start_date.strftime('%d/%m/%Y')
                end_str = record.x_end_date.strftime('%d/%m/%Y')
                record.x_exploitation_period_text = f"Từ ngày {start_str} đến ngày {end_str}"
            else:
                record.x_exploitation_period_text = ""

    @api.depends('x_contract_date', 'x_start_date', 'date_received', 'partner_id', 'company_id.x_wood_prefix')
    def _compute_contract_number(self):
        for record in self:
            if not record.partner_id:
                record.x_contract_number = False
                continue

            date_ref = record.x_contract_date or record.x_start_date or record.date_received or fields.Date.today()
            year = date_ref.year
            
            prefix = record.company_id.x_wood_prefix or "QTP"
            
            # Lấy chữ cái viết tắt của chủ rừng (Không dấu)
            name_no_accent = no_accent_vietnamese(record.partner_id.name).replace('_', ' ')
            initials = "".join(word[0] for word in name_no_accent.split() if word).upper()
            
            # Định dạng: [NgàyTháng]/[Năm]/HD-[Tiền tố]-[Viết tắt]
            day_month = date_ref.strftime('%d%m')
            record.x_contract_number = f"{day_month}/{year}/HD-{prefix}-{initials}"

    @api.depends('x_contract_date', 'x_start_date', 'company_id.x_wood_prefix', 'partner_id.name')
    def _compute_addendum_num(self):
        for record in self:
            if not record.partner_id:
                record.x_addendum_num = False
                continue
            
            date_ref = record.x_contract_date or record.x_start_date or record.date_received or fields.Date.today()
            date_str = date_ref.strftime('%d/%m/%Y')
            prefix = record.company_id.x_wood_prefix or "DL"
            
            # Lấy chữ cái viết tắt của chủ rừng (Không dấu)
            name_no_accent = no_accent_vietnamese(record.partner_id.name).replace('_', ' ')
            initials = "".join(word[0] for word in name_no_accent.split() if word).upper()
            
            record.x_addendum_num = f"{date_str}_{prefix}_{initials}"

    @api.depends('x_contract_date', 'x_start_date', 'date_received', 'partner_id')
    def _compute_x_bkls_number(self):
        for record in self:
            if not record.partner_id:
                record.x_bkls_number = False
                continue
            
            if record.x_bkls_number:
                continue

            # Xác định năm Y
            date_ref = record.x_contract_date or record.x_start_date or record.date_received or fields.Date.today()
            year = date_ref.year
            
            # Tìm số thứ tự X lớn nhất của các bảng kê cùng chủ rừng trong năm Y
            domain = [
                ('partner_id', '=', record.partner_id.id),
                ('id', '!=', record.id or 0),
            ]
            start_of_year = fields.Date.to_date(f"{year}-01-01")
            end_of_year = fields.Date.to_date(f"{year}-12-31")
            
            domain += [
                '|',
                '&', ('x_contract_date', '>=', start_of_year), ('x_contract_date', '<=', end_of_year),
                '|',
                '&', ('x_start_date', '>=', start_of_year), ('x_start_date', '<=', end_of_year),
                '&', ('x_start_date', '=', False), '&', ('date_received', '>=', start_of_year), ('date_received', '<=', end_of_year)
            ]
            
            other_dossiers = self.search(domain, order='create_date asc, id asc')
            
            max_x = 0
            for od in other_dossiers:
                if od.x_bkls_number:
                    parts = od.x_bkls_number.split('/')
                    if len(parts) >= 3:
                        try:
                            val = int(parts[0])
                            if val > max_x:
                                max_x = val
                        except ValueError:
                            pass
            
            next_x = max_x + 1
            record.x_bkls_number = f"{next_x:03d}/{year}/BKLS"
    
    # Thông tin Phương án (PAKT)
    x_pakt_date = fields.Date(string='Ngày lập PAKT')
    x_pakt_representative = fields.Char(string='Người đại diện')
    x_pakt_position = fields.Char(string='Chức vụ')

    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('exploiting', 'Đang khai thác'),
        ('using', 'Đang sử dụng'),
        ('summary', 'Tổng Kết'),
        ('confirmed', 'Xác Nhận')
    ], string='Trạng thái', default='draft', tracking=True)

    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company)
    x_woodpro_id = fields.Char(string='ID WoodPro', index=True)

    # Sản phẩm đại diện (để map với product_id của ledger)
    product_id = fields.Many2one('product.product', string='Sản phẩm đại diện', help='Dùng để map với Sổ cái (Ledger)')

    # Chi tiết loài gỗ và khối lượng theo hồ sơ
    line_ids = fields.One2many('dl.wood.dossier.line', 'dossier_id', string='Chi tiết loài gỗ')
    initial_qty = fields.Float(string='Tổng Gỗ (m³)', compute='_compute_initial_qty', store=True, digits=(16, 2))
    initial_wood_qty = fields.Float(string='Tổng Gỗ (m³)', compute='_compute_initial_qty', store=True, digits=(16, 2))
    initial_firewood_qty = fields.Float(string='Tổng Củi (Ster)', compute='_compute_initial_qty', store=True, digits=(16, 2))
    
    total_wood_amount = fields.Float(string='Tổng Tiền Gỗ', compute='_compute_amounts', store=True, digits=(16, 2))
    total_firewood_amount = fields.Float(string='Tổng Tiền Củi', compute='_compute_amounts', store=True, digits=(16, 2))
    total_amount = fields.Float(string='Tổng Cộng Thành Tiền', compute='_compute_amounts', store=True, digits=(16, 2))


    # Tệp đính kèm
    x_internal_attachment_ids = fields.Many2many('ir.attachment', string='Tệp Đính Kèm (Hệ Thống)')
    attachment_ids = fields.One2many('dl.wood.dossier.attachment', 'dossier_id', string='Tệp đính kèm (WoodPro)')

    # Danh sách 8 tài liệu hệ thống cố định
    document_ids = fields.One2many('dl.wood.dossier.document', 'dossier_id', string='Tài liệu hệ thống')

    # Thông tin Vận chuyển
    transport_ids = fields.One2many('dl.wood.dossier.transport', 'dossier_id', string='Cấu hình vận chuyển')
    ticket_ids = fields.One2many('dl.wood.dossier.transport.ticket', 'dossier_id', string='Danh sách phiếu nhập kho')

    # -------------------------------------------------------------------------
    # Ledger Relation & Stock Calculation
    # -------------------------------------------------------------------------
    ledger_ids = fields.One2many('dl.dossier.ledger', 'dossier_id', string='Sổ Cái Biến Động')

    remaining_qty = fields.Float(string='Tồn Kho Thực Tế (m³)', compute='_compute_stock_quantities', store=True, digits=(16, 2))
    qty_reserved = fields.Float(string='Đang Giữ Đơn (m³)', compute='_compute_stock_quantities', store=True, digits=(16, 2))
    qty_available = fields.Float(string='Khả Dụng Để Bán (m³)', compute='_compute_stock_quantities', store=True, digits=(16, 2))
    qty_consumed = fields.Float(string='Đã Tiêu Hao (m³)', compute='_compute_stock_quantities', store=True, digits=(16, 2))

    x_production_ids = fields.Many2many(
        'dl.wood.production.order',
        string='Lệnh sản xuất liên quan',
        compute='_compute_x_production_ids',
        help='Các lệnh sản xuất đã tiêu hao nguyên vật liệu từ hồ sơ này.'
    )
    x_production_count = fields.Integer(
        string='Số lệnh sản xuất',
        compute='_compute_x_production_ids'
    )

    @api.depends('line_ids.price_subtotal', 'line_ids.wood_type')
    def _compute_amounts(self):
        for dossier in self:
            wood_lines = dossier.line_ids.filtered(lambda l: l.wood_type == 'wood')
            firewood_lines = dossier.line_ids.filtered(lambda l: l.wood_type == 'firewood')
            
            dossier.total_wood_amount = sum(wood_lines.mapped('price_subtotal'))
            dossier.total_firewood_amount = sum(firewood_lines.mapped('price_subtotal'))
            dossier.total_amount = dossier.total_wood_amount + dossier.total_firewood_amount

    @api.depends('initial_wood_qty', 'ledger_ids.actual_qty', 'ledger_ids.state')
    def _compute_stock_quantities(self):
        for dossier in self:
            done_lines = dossier.ledger_ids.filtered(lambda l: l.state == 'done')
            draft_lines = dossier.ledger_ids.filtered(lambda l: l.state == 'draft')
            # Chỉ tính tồn kho GỖ (m³). Củi không có tồn kho trong hệ thống.
            dossier.remaining_qty = round(dossier.initial_wood_qty + sum(done_lines.mapped('actual_qty')), 2)
            dossier.qty_reserved = round(abs(sum(draft_lines.mapped('actual_qty'))), 2)
            dossier.qty_available = round(dossier.remaining_qty - dossier.qty_reserved, 2)
            dossier.qty_consumed = round(max(0.0, dossier.initial_wood_qty - dossier.remaining_qty), 2)

    @api.depends('ledger_ids.production_id')
    def _compute_x_production_ids(self):
        for dossier in self:
            # Sử dụng sudo() để lấy tất cả lệnh sản xuất mà không bị chặn bởi phân quyền đa công ty
            ledgers = dossier.ledger_ids.sudo()
            prod_orders = ledgers.filtered(lambda l: l.production_id).mapped('production_id')
            
            # Để tránh lỗi AccessError khi hiển thị Many2many trên giao diện của user,
            # chúng ta chỉ gán những lệnh sản xuất thuộc công ty mà user hiện tại được phép truy cập.
            allowed_company_ids = self.env.companies.ids
            accessible_prod_orders = prod_orders.filtered(lambda p: p.company_id.id in allowed_company_ids)
            
            dossier.x_production_ids = accessible_prod_orders
            dossier.x_production_count = len(prod_orders)

    @api.model
    def default_get(self, fields_list):
        res = super(DlWoodDossier, self).default_get(fields_list)
        if 'partner_id' in res and res.get('partner_id'):
            partner = self.env['res.partner'].browse(res['partner_id'])
            if partner:
                company_id = res.get('company_id') or self.env.company.id
                company = self.env['res.company'].browse(company_id)
                if 'x_prep_days' in fields_list and not res.get('x_prep_days'):
                    res['x_prep_days'] = partner.x_prep_days or (company and company.x_prep_days) or 6
                if 'x_exploitation_capacity' in fields_list and not res.get('x_exploitation_capacity'):
                    res['x_exploitation_capacity'] = partner.x_exploitation_capacity or (company and company.x_exploitation_capacity) or 40
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'partner_id' in vals and vals.get('partner_id'):
                partner = self.env['res.partner'].browse(vals['partner_id'])
                if partner:
                    if not vals.get('x_owner_representative'):
                        vals['x_owner_representative'] = partner.name
                    if not vals.get('x_prep_days'):
                        company_id = vals.get('company_id') or self.env.company.id
                        company = self.env['res.company'].browse(company_id)
                        vals['x_prep_days'] = partner.x_prep_days or (company and company.x_prep_days) or 6
                    if not vals.get('x_exploitation_capacity'):
                        company_id = vals.get('company_id') or self.env.company.id
                        company = self.env['res.company'].browse(company_id)
                        vals['x_exploitation_capacity'] = partner.x_exploitation_capacity or (company and company.x_exploitation_capacity) or 40
                    
        records = super(DlWoodDossier, self).create(vals_list)
        for record in records:
            # Tự động tạo tài liệu mẫu khi tạo hồ sơ mới
            record._init_default_documents()
        return records

    def action_generate_transport_tickets(self):
        """Thuật toán tự động sinh chuyến xe dựa trên cấu hình vận chuyển đa phương tiện (Multi-Vehicle Split Algorithm)
        Đã nâng cấp: tối ưu hóa xếp xe dồn chuyến để tránh trường hợp chuyến cuối lẻ quá ít củi/gỗ.
        Tách biệt xe chở gỗ và xe chở củi hoàn toàn. Giao gỗ trước, củi sau.
        """
        import random
        import math
        import datetime
        from odoo.exceptions import UserError
        from odoo import fields, _

        def find_optimal_vehicles(fleet, total_volume):
            """Hàm helper tìm danh sách xe tối ưu để chở hết total_volume
            Sử dụng tỷ lệ lấp đầy tối đa lên tới 100% để dồn chuyến nếu giúp tiết kiệm xe/chuyến.
            """
            if total_volume <= 0 or not fleet:
                return []
            
            # 1. Tính số xe cần thiết theo chế độ bình thường (lấp đầy <= 90% hoặc theo fill_rate_max của xe)
            normal_vehicles = []
            normal_cap = 0.0
            idx = 0
            while normal_cap < total_volume:
                v = fleet[idx % len(fleet)]
                normal_vehicles.append(v)
                fill_rate_normal = (v.get('fill_rate_max', 90.0) or 90.0) / 100.0
                normal_cap += v['capacity'] * fill_rate_normal
                idx += 1
                
            # 2. Tính số xe tối thiểu theo chế độ tối đa (100% capacity)
            max_vehicles = []
            max_cap = 0.0
            idx = 0
            while max_cap < total_volume:
                v = fleet[idx % len(fleet)]
                max_vehicles.append(v)
                max_cap += v['capacity'] * 1.0
                idx += 1
                
            # Nếu chế độ tối đa (100%) giúp giảm số xe so với chế độ bình thường
            if len(max_vehicles) < len(normal_vehicles):
                return max_vehicles
            
            # Nếu số xe bằng nhau, thử dồn chuyến nếu bỏ xe cuối cùng đi mà vẫn đủ sức chứa 100%
            if len(normal_vehicles) > 1:
                reduced_vehicles = normal_vehicles[:-1]
                reduced_capacity = sum(v['capacity'] for v in reduced_vehicles)
                if reduced_capacity >= total_volume:
                    return reduced_vehicles
                    
            return normal_vehicles

        def allocate_volume_to_vehicles(vehicles, total_volume):
            """Hàm helper phân bổ đều khối lượng cho danh sách xe đã chọn
            Có độ biến thiên tải trọng ngẫu nhiên +/- 4% để tạo tính thực tế.
            Đảm bảo tổng khối lượng khớp chính xác và không xe nào chở quá 100% capacity.
            """
            total_capacity = sum(v['capacity'] for v in vehicles)
            if total_capacity <= 0:
                return [0.0] * len(vehicles)
            
            avg_fill = total_volume / total_capacity
            
            # Gán tỷ lệ lấp đầy ngẫu nhiên biến thiên nhẹ quanh avg_fill
            raw_vols = []
            for v in vehicles:
                factor = random.uniform(0.96, 1.04)
                fill = avg_fill * factor
                fill = max(0.01, min(1.0, fill))
                raw_vols.append(v['capacity'] * fill)
                
            # Chuẩn hóa để tổng bằng total_volume
            sum_raw = sum(raw_vols)
            if sum_raw > 0:
                v_volumes = [round((vol / sum_raw) * total_volume, 1) for vol in raw_vols]
            else:
                v_volumes = [round((v['capacity'] / total_capacity) * total_volume, 1) for v in vehicles]
                
            # Khống chế không xe nào vượt quá 100% capacity
            for _ in range(5):
                diff = total_volume - sum(v_volumes)
                if abs(diff) < 0.05:
                    v_volumes[-1] = round(v_volumes[-1] + diff, 1)
                    diff = 0
                    
                has_overflow = False
                for idx, v in enumerate(vehicles):
                    if v_volumes[idx] > v['capacity']:
                        overflow = v_volumes[idx] - v['capacity']
                        v_volumes[idx] = v['capacity']
                        has_overflow = True
                        available_indices = [i for i, x in enumerate(vehicles) if i != idx and v_volumes[i] < x['capacity']]
                        if available_indices:
                            share = overflow / len(available_indices)
                            for ai in available_indices:
                                v_volumes[ai] = round(v_volumes[ai] + share, 1)
                if not has_overflow and abs(diff) < 0.01:
                    break
                    
            # Khớp tuyệt đối tổng total_volume do sai số làm tròn
            diff = round(total_volume - sum(v_volumes), 1)
            if diff != 0:
                for idx, v in enumerate(vehicles):
                    if v_volumes[idx] + diff <= v['capacity']:
                        v_volumes[idx] = round(v_volumes[idx] + diff, 1)
                        diff = 0
                        break
                if diff != 0:
                    v_volumes[-1] = round(v_volumes[-1] + diff, 1)
            
            # Hard cap cuối cùng: không xe nào được vượt quá 100% capacity tuyệt đối
            for idx, v in enumerate(vehicles):
                if v_volumes[idx] > v['capacity']:
                    v_volumes[idx] = v['capacity']
                    
            return v_volumes

        def calculate_ticket_date(start_date, days_offset):
            """Hàm helper tính ngày vận chuyển thực tế loại trừ Chủ Nhật"""
            curr = start_date
            if curr.weekday() == 6:
                curr += datetime.timedelta(days=1)
            for _ in range(days_offset):
                curr += datetime.timedelta(days=1)
                while curr.weekday() == 6:
                    curr += datetime.timedelta(days=1)
            return curr

        for dossier in self:
            if dossier.state in ('using', 'summary', 'confirmed'):
                raise UserError(_("Không thể thực hiện tính toán chia lại phiếu nhập kho khi Hồ sơ gỗ đang ở trạng thái '%s'.") % dossier.state)
            
            start_date = dossier.x_delivery_start_date or fields.Date.today()
            end_date = dossier.x_delivery_end_date or fields.Date.today()
            
            # 1. Xóa tickets cũ
            dossier.ticket_ids.unlink()

            if not dossier.transport_ids:
                continue

            # 2. Xây dựng danh sách toàn bộ xe có sẵn trong đội xe (fleet)
            fleet = []
            for t in dossier.transport_ids:
                if not t.vehicle_id or t.vehicle_count <= 0 or t.vehicle_id.capacity <= 0:
                    continue
                for _ in range(t.vehicle_count):
                    fleet.append({
                        'id': t.vehicle_id.id,
                        'name': t.vehicle_id.name,
                        'capacity': t.vehicle_id.capacity,
                        'fill_rate_min': t.vehicle_id.fill_rate_min if t.vehicle_id.fill_rate_min else 90.0,
                        'fill_rate_max': t.vehicle_id.fill_rate_max if t.vehicle_id.fill_rate_max else 95.0
                    })
                    
            if not fleet:
                continue
                
            # Sắp xếp đội xe giảm dần theo sức chở để ưu tiên xe lớn trước
            fleet.sort(key=lambda x: x['capacity'], reverse=True)
            fleet_size = len(fleet)

            # 3. Chuẩn bị dữ liệu gỗ và củi cần vận chuyển
            wood_lines = [{'id': l.species_id.id, 'wood_type': l.wood_type, 'remaining': l.volume} 
                          for l in dossier.line_ids.filtered(lambda x: x.wood_type == 'wood' and x.volume > 0)]
            firewood_lines = [{'id': l.species_id.id, 'wood_type': l.wood_type, 'remaining': l.volume_ster} 
                              for l in dossier.line_ids.filtered(lambda x: x.wood_type == 'firewood' and x.volume_ster > 0)]

            total_wood = sum(x['remaining'] for x in wood_lines)
            total_firewood = sum(x['remaining'] for x in firewood_lines)
            
            if total_wood <= 0 and total_firewood <= 0:
                continue

            # 4. Tìm danh sách xe tối ưu cho gỗ và củi
            optimal_wood_vehicles = find_optimal_vehicles(fleet, total_wood)
            optimal_firewood_vehicles = find_optimal_vehicles(fleet, total_firewood)

            # Phân bổ khối lượng thực tế cho từng xe
            wood_vols = allocate_volume_to_vehicles(optimal_wood_vehicles, total_wood)
            for idx, v in enumerate(optimal_wood_vehicles):
                # Copy dict xe để tránh ghi đè chéo và thêm unique_idx + type để gom chung
                optimal_wood_vehicles[idx] = dict(v, allocated_volume=wood_vols[idx], unique_idx=idx, type='wood')

            firewood_vols = allocate_volume_to_vehicles(optimal_firewood_vehicles, total_firewood)
            for idx, v in enumerate(optimal_firewood_vehicles):
                optimal_firewood_vehicles[idx] = dict(v, allocated_volume=firewood_vols[idx], unique_idx=idx, type='firewood')

            # Gộp chung toàn bộ chuyến gỗ và củi lại thành một danh sách chuyến đi tối ưu chung
            optimal_all_vehicles = optimal_wood_vehicles + optimal_firewood_vehicles

            # 5. Gom nhóm xe theo ngày dựa trên cách vận chuyển
            method = dossier.x_transport_method or 'normal'
            if method == 'urgent':
                chunk_size = fleet_size * 2
            else:
                chunk_size = fleet_size

            trips = []
            for i in range(0, len(optimal_all_vehicles), chunk_size):
                chunk = optimal_all_vehicles[i:i + chunk_size]
                trips.append({
                    'vehicles': chunk
                })

            tickets_vals = []
            trip_counter = 1

            # Khởi tạo Pool hàng hóa để rút dần
            wood_pool = [{'species_id': w['id'], 'remaining': w['remaining']} for w in wood_lines]
            firewood_pool = [{'species_id': f['id'], 'remaining': f['remaining']} for f in firewood_lines]

            # Bản đồ theo dõi lượng hàng ban đầu và lượng đã phân bổ để bù sai số làm tròn Ticket lines
            initial_volume_map = {}
            for l in dossier.line_ids:
                key = (l.species_id.id, l.wood_type)
                val = l.volume_ster if l.wood_type == 'firewood' else l.volume
                if val > 0:
                    initial_volume_map[key] = initial_volume_map.get(key, 0.0) + val

            ticket_allocated_map = {}

            for trip in trips:
                vehicles_in_trip = trip['vehicles']
                vehicle_lines = []
                ticket_lines_map = {}

                for v in vehicles_in_trip:
                    v_target = v['allocated_volume']
                    v_remaining = v_target
                    v_species_lines = []

                    cargo_pool = wood_pool if v['type'] == 'wood' else firewood_pool
                    optimal_list = optimal_wood_vehicles if v['type'] == 'wood' else optimal_firewood_vehicles
                    is_last_vehicle = (v.get('unique_idx') == optimal_list[-1].get('unique_idx'))

                    if is_last_vehicle:
                        # Kiểm tra: pool còn lại có vừa vào xe này không?
                        # Nếu pool > capacity → xe này KHÔNG phải xe cuối thực sự
                        # → xử lý như xe bình thường, giới hạn ở v_target
                        pool_remaining = sum(item['remaining'] for item in cargo_pool if item['remaining'] > 0.0)
                        if pool_remaining > v['capacity']:
                            is_last_vehicle = False  # downgrade về xe bình thường

                    if is_last_vehicle:
                        # Xe cuối thực sự của loại hàng: lấy nốt toàn bộ hàng còn lại trong Pool
                        for item in cargo_pool:
                            if item['remaining'] > 0.0:
                                v_species_lines.append({
                                    'species_id': item['species_id'],
                                    'volume': item['remaining']
                                })
                                item['remaining'] = 0.0
                    else:
                        # Xe bình thường: Phân bổ hàng theo v_remaining (không vượt capacity)
                        for item in cargo_pool:
                            if v_remaining <= 0.0:
                                break
                            if item['remaining'] > 0.0:
                                take = round(min(item['remaining'], v_remaining), 1)
                                if take > 0.0:
                                    v_species_lines.append({
                                        'species_id': item['species_id'],
                                        'volume': take
                                    })
                                    item['remaining'] = round(item['remaining'] - take, 1)
                                    v_remaining = round(v_remaining - take, 1)
                        
                        # Nếu vẫn còn thiếu ít tải trọng do làm tròn, bù thêm từ loài gỗ đầu tiên còn hàng
                        if v_remaining > 0.0:
                            for item in cargo_pool:
                                if item['remaining'] > 0.0:
                                    take = round(min(item['remaining'], v_remaining), 1)
                                    if take > 0.0:
                                        found = False
                                        for line in v_species_lines:
                                            if line['species_id'] == item['species_id']:
                                                line['volume'] = round(line['volume'] + take, 1)
                                                found = True
                                                break
                                        if not found:
                                            v_species_lines.append({
                                                'species_id': item['species_id'],
                                                'volume': take
                                            })
                                        item['remaining'] = round(item['remaining'] - take, 1)
                                        v_remaining = round(v_remaining - take, 1)
                                    break

                    # Tạo các dòng chi tiết phương tiện của xe này
                    for line in v_species_lines:
                        if line['volume'] > 0:
                            vehicle_lines.append({
                                'name': v['name'],
                                'capacity': v['capacity'],
                                'volume': line['volume'],
                                'species_id': line['species_id'],
                                'wood_type': v['type'],
                            })
                            key = (line['species_id'], v['type'])
                            ticket_lines_map[key] = ticket_lines_map.get(key, 0.0) + line['volume']

                # Gom các dòng phương tiện lại theo species_id để tạo dòng ticket_line_ids
                lines_to_create = []
                for key, vol_sum in ticket_lines_map.items():
                    species_id, w_type = key
                    init_vol = initial_volume_map.get(key, 0.0)
                    
                    cargo_pool = wood_pool if w_type == 'wood' else firewood_pool
                    remaining_in_pool = sum(item['remaining'] for item in cargo_pool if item['species_id'] == species_id)
                    accumulated = ticket_allocated_map.get(key, 0.0)
                    
                    if remaining_in_pool <= 0.01:
                        # Xe cuối cùng của loài này đã được phân bổ trong chuyến này -> lấy nốt phần còn lại để khớp tuyệt đối
                        vol_to_assign = round(init_vol - accumulated, 1)
                        # Bù sai số cho dòng phương tiện cuối cùng chở loài gỗ này
                        diff = round(vol_to_assign - vol_sum, 1)
                        if diff != 0:
                            for vl in reversed(vehicle_lines):
                                if vl['species_id'] == species_id and vl['wood_type'] == w_type:
                                    vl['volume'] = round(vl['volume'] + diff, 1)
                                    break
                    else:
                        vol_to_assign = round(vol_sum, 1)
                        
                    vol_to_assign = max(0.1, vol_to_assign)
                    
                    lines_to_create.append({
                        'species_id': species_id,
                        'wood_type': w_type,
                        'volume': vol_to_assign
                    })
                    ticket_allocated_map[key] = accumulated + vol_to_assign

                if lines_to_create:
                    # Tính ngày vận chuyển thực tế dựa trên chế độ vận chuyển x_transport_method
                    if method == 'slow':
                        days_offset = (trip_counter - 1) * 2
                    else:
                        days_offset = trip_counter - 1

                    ticket_date = calculate_ticket_date(start_date, days_offset)
                    if ticket_date > end_date:
                        ticket_date = end_date

                    date_str = ticket_date.strftime('%d/%m/%Y')
                    ticket_name = f"Phiếu ngày {date_str}"

                    total_trip_vol = sum(line['volume'] for line in lines_to_create)
                    nominal_cap = sum(v['capacity'] for v in vehicles_in_trip)
                    fill_rate = round((total_trip_vol / nominal_cap), 4) if nominal_cap > 0 else 0.0

                    tickets_vals.append({
                        'dossier_id': dossier.id,
                        'name': ticket_name,
                        'x_date': ticket_date,
                        'vehicle_count': len(vehicles_in_trip),
                        'x_vehicle_info': ", ".join([v['name'] for v in vehicles_in_trip]),
                        'x_vehicle_capacities': ", ".join([str(v['capacity']) for v in vehicles_in_trip]),
                        'fill_rate': fill_rate,
                        'ticket_line_ids': [(0, 0, vals) for vals in lines_to_create],
                        'x_vehicle_ids': [(0, 0, vals) for vals in vehicle_lines]
                    })
                    trip_counter += 1

            if tickets_vals:
                self.env['dl.wood.dossier.transport.ticket'].create(tickets_vals)

    @api.onchange('x_start_date', 'line_ids', 'x_prep_days', 'x_exploitation_capacity')
    def _onchange_suggest_end_date(self):
        """Tự động gợi ý ngày kết thúc khai thác dựa trên ngày bắt đầu, năng lực khai thác và thời gian chuẩn bị."""
        if self.x_start_date:
            import math
            # Lấy cấu hình 3 cấp (Ưu tiên: Hồ sơ -> Chủ rừng -> Công ty)
            prep_days = self.x_prep_days or (self.partner_id and self.partner_id.x_prep_days) or (self.company_id and self.company_id.x_prep_days) or 6
            capacity = self.x_exploitation_capacity or (self.partner_id and self.partner_id.x_exploitation_capacity) or (self.company_id and self.company_id.x_exploitation_capacity) or 40

            # Chỉ tính khối lượng GỖ (m³) để ước tính thời gian khai thác.
            # Củi (volume_ster) không tham gia vào ước tính này.
            total_vol = sum(l.volume for l in self.line_ids if l.wood_type == 'wood')
            
            # Tính số ngày khai thác cần thiết
            exploitation_days = math.ceil(total_vol / capacity) if capacity > 0 else 1
            days_needed = prep_days + exploitation_days
            
            if days_needed < 1:
                days_needed = 1
                
            from datetime import timedelta
            # inclusive date calculation (ví dụ: ngày 01 đến 08 là mất 8 ngày, tức 01 + 7 ngày)
            self.x_end_date = self.x_start_date + timedelta(days=max(0, days_needed - 1))


    @api.onchange('partner_id')
    def _onchange_partner_id_populate_rep(self):
        """Tự động điền người đại diện chủ rừng mặc định khi chọn chủ rừng."""
        if self.partner_id:
            self.x_owner_representative = self.partner_id.name
            
            # Kế thừa năng lực khai thác và thời gian chuẩn bị từ Chủ rừng
            # Nếu chủ rừng chưa cấu hình (bằng 0), fallback về cấu hình mặc định của công ty
            self.x_prep_days = self.partner_id.x_prep_days or self.company_id.x_prep_days or 6
            self.x_exploitation_capacity = self.partner_id.x_exploitation_capacity or self.company_id.x_exploitation_capacity or 40
            
            # Tự động chọn địa bàn khai thác mặc định
            locations = self.partner_id.exploitation_location_ids
            if locations:
                main_loc = locations.filtered(lambda l: l.is_main)
                if main_loc:
                    self.exploitation_location_id = main_loc[0]
                elif len(locations) == 1:
                    self.exploitation_location_id = locations[0]
                else:
                    self.exploitation_location_id = False
            else:
                self.exploitation_location_id = False
                
            # Cập nhật diện tích nếu địa bàn được chọn
            if self.exploitation_location_id:
                self._onchange_exploitation_location_id()

    @api.onchange('exploitation_location_id')
    def _onchange_exploitation_location_id(self):
        """Tự động điền diện tích và danh sách loài gỗ khi thay đổi địa bàn khai thác.
        
        - Luôn cập nhật diện tích (x_area) từ địa điểm.
        - Chỉ tự động điền line_ids nếu chưa có dòng nào (tránh ghi đè dữ liệu đã nhập).
        - Tự động tìm phân loại (grade) đầu tiên theo logic chuẩn.
        """
        if self.exploitation_location_id:
            self.x_area = self.exploitation_location_id.x_area_ha
            
            # Chỉ điền loài gỗ mặc định khi chưa có chi tiết khai thác
            if not self.line_ids and self.exploitation_location_id.species_ids:
                GradeModel = self.env['dl.wood.species.grade']
                new_lines = []
                for spec_line in self.exploitation_location_id.species_ids.sorted('sequence'):
                    species = spec_line.species_id
                    first_grade = GradeModel.search([('species_id', '=', species.id)], limit=1)
                    line_vals = {'species_id': species.id}
                    if species.wood_type == 'firewood':
                        # Củi: không cần grade, lấy giá từ grade đầu tiên nếu có
                        if first_grade:
                            line_vals['price_unit'] = first_grade.default_price
                    else:
                        # Gỗ: tự động gán grade đầu tiên + thông số kích thước
                        if first_grade:
                            line_vals['grade_id'] = first_grade.id
                            line_vals['diameter_min'] = first_grade.diameter_min
                            line_vals['diameter_max'] = first_grade.diameter_max
                            line_vals['height'] = first_grade.height
                            line_vals['price_unit'] = first_grade.default_price
                    new_lines.append((0, 0, line_vals))
                self.line_ids = new_lines


    @api.onchange('x_report_version_id')
    def _onchange_report_version_id(self):
        """Tự động nạp danh sách tài liệu khi đổi phiên bản"""
        if self.x_report_version_id:
            # Xóa các document cũ
            self.document_ids = [(5, 0, 0)]
            # Tạo mới dựa trên config của version (bao gồm cả các bản ghi không sử dụng)
            new_docs = []
            for config in self.x_report_version_id.template_config_ids:
                if not config.template_key:
                    continue
                new_docs.append((0, 0, {
                    'name': config.name,
                    'template_key': config.template_key,
                    'x_category': config.category,
                    'config_id': config.id,
                    'x_is_selected': config.is_enabled,
                    'is_enabled': config.is_enabled,
                    'sequence': config.sequence,
                }))
            self.document_ids = new_docs

    def action_refresh_documents(self):
        """Nút bấm thủ công để nạp lại danh sách tài liệu theo phiên bản hiện tại"""
        self.ensure_one()
        self._onchange_report_version_id()

    def _init_default_documents(self):
        """Khởi tạo danh sách tài liệu mặc định (sử dụng phiên bản mặc định)"""
        if not self.x_report_version_id:
            # Tìm phiên bản mặc định của công ty
            default_version = self.env['dl.wood.report.version'].search([
                ('company_id', '=', self.company_id.id)
            ], limit=1, order='id desc')
            if default_version:
                self.x_report_version_id = default_version
        
        if self.x_report_version_id and not self.document_ids:
            self._onchange_report_version_id()

    @api.depends('partner_id.x_full_address')
    def _compute_partner_address(self):
        for record in self:
            record.partner_address = record.partner_id.x_full_address or ""

    @api.depends('line_ids.volume', 'line_ids.volume_ster', 'line_ids.wood_type')
    def _compute_initial_qty(self):
        for record in self:
            # Tổng gỗ tính theo m³ (volume)
            record.initial_wood_qty = round(
                sum(record.line_ids.filtered(lambda l: l.wood_type == 'wood').mapped('volume')), 2
            )
            # Tổng củi tính theo Ster (volume_ster) — khác đơn vị, không cộng chung
            record.initial_firewood_qty = round(
                sum(record.line_ids.filtered(lambda l: l.wood_type == 'firewood').mapped('volume_ster')), 2
            )
            # initial_qty CHỈ là gỗ (m³) — dùng cho tồn kho và vận chuyển gỗ
            record.initial_qty = record.initial_wood_qty

    # --- QUẢN LÝ TRẠNG THÁI (STATE MACHINE) ---
    def action_draft(self):
        self.write({'state': 'draft'})

    def action_exploiting(self):
        self.write({'state': 'exploiting'})

    def action_using(self):
        self.write({'state': 'using'})

    def action_summary(self):
        self.write({'state': 'summary'})

    def action_confirm(self):
        for record in self:
            if not record.line_ids:
                raise UserError(_("Vui lòng nhập chi tiết loại gỗ trước khi xác nhận."))
        self.write({'state': 'confirmed'})

    # --- XUẤT FILE WORD (Tách logic render sang dl_wood_dossier_renderer.py) ---
    def _get_template_source(self, template_key):
        """Tìm nguồn template: Tạm thời lấy trực tiếp từ ổ đĩa (static/TEMPLATES/) để sửa đổi nhanh chóng."""
        self.ensure_one()
        key_aliases = {
            # Hợp đồng hồ sơ nguồn gốc
            'hdhsg': 'hd_hsg',
            'hdsg': 'hd_hsg',
            'hop_dong_hsg': 'hd_hsg',
            'hop_dong_ho_so_nguon_goc': 'hd_hsg',
            
            # Phương án khai thác
            'pakt': 'pakt',
            'phuong_an_khai_thac': 'pakt',
            
            # Phiếu thông tin khai thác (ptkt)
            'ptkt': 'pakt',  # ptkt tạm dùng chung mẫu với pakt nếu chưa có mẫu riêng
            'phieu_thong_tin_khai_thac': 'pakt',
            
            # Bảng kê lâm sản
            'bkls': 'bkls',
            'ban_ke_lam_san': 'bkls',
            'bang_ke_lam_san': 'bkls',
            
            # Bảng kê lâm sản chia nhỏ
            'cn_bkls': 'cn_bkls',
            'chia_nho_bkls': 'cn_bkls',
            
            # Đơn đề nghị xác nhận
            'ddnx': 'xn_bkls',
            'don_de_nghi_xac_nhan': 'xn_bkls',
            'xac_nhan_bkls': 'xn_bkls',
            'xn_bkls': 'xn_bkls',
            
            # Biên bản xác minh
            'bbxm': 'bbxm',
            'bien_ban_xac_minh': 'bbxm',
            'bien_ban_xac_minh_ngls': 'bb_xm_ngls',
            
            # Các mẫu khác (nếu tải lên sau này)
            'cnbk': 'cnbk',
            'cam_ket_nguon_goc': 'cnbk',
            'pnk': 'phieu_nhap_kho',
            'phieu_nhap_kho': 'phieu_nhap_kho',
            'bbbg': 'bbbg',
            'bien_ban_ban_giao': 'bbbg',
            'gbn': 'gbn',
            'giay_ban_no': 'gbn'
        }
        disk_key = key_aliases.get(template_key, template_key)
        template_filename = f"TEMPLATE_{disk_key.upper()}.docx"
        try:
            path = tools.file_path(f'dl_wood_traceability/static/TEMPLATES/{template_filename}')
            _logger.info("[_get_template_source] [BYPASS DB] template_key='%s' → lấy trực tiếp từ ổ đĩa: %s",
                         template_key, path)
            return path
        except FileNotFoundError:
            # Dự phòng cho trường hợp gõ sai chính tả TEMPATE thay vì TEMPLATE
            try:
                alt_filename = f"TEMPATE_{disk_key.upper()}.docx"
                path = tools.file_path(f'dl_wood_traceability/static/TEMPLATES/{alt_filename}')
                _logger.info("[_get_template_source] [BYPASS DB] [ALT] template_key='%s' → lấy trực tiếp từ ổ đĩa: %s",
                             template_key, path)
                return path
            except FileNotFoundError:
                raise UserError(
                    _("Không tìm thấy file mẫu cho tài liệu '%s' (tên file: %s hoặc %s) trong thư mục static/TEMPLATES/.") 
                    % (template_key, template_filename, f"TEMPATE_{disk_key.upper()}.docx")
                )

    def _render_docx(self, template_key):
        """Render file .docx: tìm template → giao DossierDocxRenderer xử lý."""
        self.ensure_one()
        template_source = self._get_template_source(template_key)
        renderer = DossierDocxRenderer(self)
        try:
            return renderer.render(template_key, template_source)
        except Exception as e:
            tb = traceback.format_exc()
            _logger.error("[_render_docx] Lỗi khi render template '%s':\n%s", template_key, tb)
            raise UserError(
                _("Lỗi định dạng hoặc không thể đọc template %s: %s\n\n"
                  "=== CHI TIẾT TRACEBACK LỖI ===\n%s") % (template_key, str(e), tb)
            )




    def action_export_pakt_docx(self):
        """Nút bấm nhanh cho PAKT (Giữ lại để tương thích view cũ nếu cần)"""
        return self._action_download_template('pakt')

    def action_download_ptkt(self): return self._action_download_template('ptkt')
    def action_download_hdsg(self): return self._action_download_template('hdsg')
    def action_download_bkls(self): return self._action_download_template('bkls')
    def action_download_cn_bkls(self): return self._action_download_template('chia_nho_bkls')
    def action_download_ddnx(self): return self._action_download_template('ddnx')
    def action_download_bbxm(self): return self._action_download_template('bbxm')
    def action_download_cnbk(self): return self._action_download_template('cnbk')
    def action_download_pnk(self): return self._action_download_template('pnk')
    def action_download_bbbg(self): return self._action_download_template('bbbg')
    def action_download_gbn(self): return self._action_download_template('gbn')

    def action_download_zip(self):
        """Tải các tài liệu đã chọn dưới dạng file nén ZIP"""
        selected_docs = self.document_ids.filtered(lambda d: d.x_is_selected)
        if not selected_docs:
            raise UserError(_("Vui lòng chọn ít nhất một tài liệu để tải ZIP."))
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/dl_wood/download_zip/{self.id}',
            'target': 'self',
        }

    def action_select_all_exploitation(self):
        self.document_ids.filtered(lambda d: d.x_category == 'exploitation').write({'x_is_selected': True})
    
    def action_deselect_all_exploitation(self):
        self.document_ids.filtered(lambda d: d.x_category == 'exploitation').write({'x_is_selected': False})

    def action_select_all_logistics(self):
        self.document_ids.filtered(lambda d: d.x_category == 'logistics').write({'x_is_selected': True})

    def action_deselect_all_logistics(self):
        self.document_ids.filtered(lambda d: d.x_category == 'logistics').write({'x_is_selected': False})

    def _action_download_template(self, template_key):
        return {
            'type': 'ir.actions.act_url',
            'url': f'/dl_wood/render_docx/{self.id}/{template_key}',
            'target': 'self',
        }

    def get_export_filename(self, template_key):
        """Tạo tên file theo format: Tiền tố_Tên không dấu_Mã hồ sơ_Ngày tải.docx"""
        self.ensure_one()
        prefix = self.company_id.x_wood_prefix or "DL"
        
        # Lấy tên hiển thị của tài liệu từ document_ids
        doc = self.document_ids.filtered(lambda d: d.template_key == template_key)
        raw_name = doc[0].name if doc else template_key.upper()
        # Loại bỏ tiền tố số (1., 2...) nếu có
        if '. ' in raw_name:
            raw_name = raw_name.split('. ', 1)[1]
            
        clean_name = no_accent_vietnamese(raw_name)
        date_str = fields.Date.today().strftime('%d%m%Y')
        
        return f"{prefix}_{clean_name}_{self.name}_{date_str}.docx"

    def _get_exploitation_address(self):
        """
        Lấy địa chỉ khai thác đầy đủ của hồ sơ (dossier).
        Ưu tiên full_address của địa điểm khai thác, sau đó đến display_name, cuối cùng là partner_address.
        """
        self.ensure_one()
        return self.exploitation_location_id.full_address or self.exploitation_location_id.display_name or self.partner_address or ""

    def write(self, vals):
        forbidden_fields = {
            'partner_id', 'exploitation_location_id', 'x_report_version_id',
            'x_dossier_name', 'x_area', 'x_mining_method',
            'date_received', 'x_start_date', 'x_end_date', 'x_contract_date',
            'x_addendum_date', 'x_bkls_date', 'x_verify_date',
            'x_delivery_start_date', 'x_delivery_end_date',
            'x_contract_number', 'x_addendum_num', 'x_bkls_number',
            'x_owner_representative', 'x_owner_position',
            'x_company_representative', 'x_company_position',
            'line_ids', 'transport_ids', 'ticket_ids'
        }
        for rec in self:
            if rec.state in ('using', 'summary', 'confirmed'):
                changed_fields = set(vals.keys())
                if changed_fields.intersection(forbidden_fields):
                    raise UserError(_(
                        "Tuyệt đối không được chỉnh sửa thông tin pháp lý, thông tin khai thác, ngày tháng, "
                        "số phụ lục hoặc các chi tiết dòng khi Hồ sơ gỗ đang ở trạng thái '%s'."
                    ) % rec.state)
        return super(DlWoodDossier, self).write(vals)

    def unlink(self):
        for rec in self:
            if rec.state in ('using', 'summary', 'confirmed'):
                raise UserError(_(
                    "Tuyệt đối không được xóa Hồ sơ gỗ khi đang ở trạng thái '%s'."
                ) % rec.state)
        return super(DlWoodDossier, self).unlink()


class DlWoodDossierDocument(models.Model):
    _name = 'dl.wood.dossier.document'
    _description = 'Tài liệu hệ thống của hồ sơ gỗ'
    _order = 'sequence, id'

    dossier_id = fields.Many2one('dl.wood.dossier', string='Hồ Sơ Gỗ', ondelete='cascade')
    sequence = fields.Integer(string='STT', default=10)
    name = fields.Char(string='Tên tài liệu', required=True)
    template_key = fields.Char(string='Mã template', related='config_id.template_key', readonly=True)
    is_enabled = fields.Boolean(string='Đang dùng', related='config_id.is_enabled', readonly=True)
    config_id = fields.Many2one('dl.wood.report.template.config', string='Cấu hình mẫu', ondelete='set null')
    x_category = fields.Selection([
        ('exploitation', 'Hồ sơ khai thác'),
        ('logistics', 'Hồ sơ vận chuyển/Bàn giao')
    ], string='Phân loại', related='config_id.category', readonly=True)
    x_is_selected = fields.Boolean(string='Chọn', default=True)
    company_id = fields.Many2one('res.company', related='dossier_id.company_id', store=True, index=True)
    
    def action_download(self):
        """Trả về URL để controller render và tải file về ngay lập tức"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/dl_wood/render_docx/{self.dossier_id.id}/{self.template_key}',
            'target': 'self',
        }

    def action_preview_pdf(self):
        """Mở tab mới để xem trước bản PDF"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/dl_wood/preview_pdf/{self.dossier_id.id}/{self.template_key}',
            'target': 'new',
        }


class DlWoodDossierLine(models.Model):
    _name = 'dl.wood.dossier.line'
    _description = 'Chi tiết loài gỗ trong hồ sơ'

    dossier_id = fields.Many2one('dl.wood.dossier', string='Hồ Sơ Gỗ', ondelete='cascade')
    partner_id = fields.Many2one('res.partner', related='dossier_id.partner_id', store=True, index=True)
    company_id = fields.Many2one('res.company', related='dossier_id.company_id', store=True, index=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    
    species_id = fields.Many2one('dl.wood.species', string='Loài gỗ', required=True)
    grade_id = fields.Many2one('dl.wood.species.grade', string='Phân loại', domain="[('species_id', '=', species_id)]")
    name = fields.Char(string='Tên loài', related='species_id.name', readonly=True)
    wood_type = fields.Selection(related='species_id.wood_type', store=True, readonly=True)
    name_en = fields.Char(string='Tên tiếng Anh', related='species_id.name_en', readonly=True)
    name_sci = fields.Char(string='Tên khoa học', related='species_id.name_sci', readonly=True)
    x_species_group = fields.Selection(related='species_id.x_species_group', string='Nhóm loài', readonly=True)
    
    quantity = fields.Integer(string='Số lượng (Cây)')
    volume = fields.Integer(string='Khối lượng (m³)')
    volume_ster = fields.Float(
        string='Khối lượng Củi (Ster)',
        digits=(16, 2),
        default=0.0,
        help='Chỉ dùng cho Củi (firewood). Đơn vị: Ster. Người dùng nhập thẳng số ster, không cần đường kính/chiều cao.'
    )
    price_unit = fields.Integer(string='Đơn giá')
    price_subtotal = fields.Float(string='Thành tiền', compute='_compute_price_subtotal', store=True, digits=(16, 2))
    
    x_remaining_qty = fields.Float(string='Tồn Kho Thực Tế (m³)', compute='_compute_stock_quantities', store=True, digits=(16, 2))
    x_qty_reserved = fields.Float(string='Khối Lượng Giữ Hàng (m³)', compute='_compute_stock_quantities', store=True, digits=(16, 2))
    x_qty_available = fields.Float(string='Khối Lượng Khả Dụng (m³)', compute='_compute_stock_quantities', store=True, digits=(16, 2))
    x_qty_consumed = fields.Float(string='Khối Lượng Đã Dùng (m³)', compute='_compute_stock_quantities', store=True, digits=(16, 2))

    @api.depends('volume', 'volume_ster', 'price_unit', 'wood_type')
    def _compute_price_subtotal(self):
        """Thành tiền: Củi tính theo volume_ster (Ster), Gỗ tính theo volume (m³)."""
        for line in self:
            qty = line.volume_ster if line.wood_type == 'firewood' else line.volume
            line.price_subtotal = round(qty * line.price_unit, 2)

    @api.depends('volume', 'volume_ster', 'wood_type', 'dossier_id.ledger_ids.actual_qty', 'dossier_id.ledger_ids.state', 'dossier_id.ledger_ids.species_id')
    def _compute_stock_quantities(self):
        for line in self:
            # Củi không có tồn kho trong hệ thống
            if line.wood_type == 'firewood':
                line.x_remaining_qty = 0.0
                line.x_qty_reserved = 0.0
                line.x_qty_available = 0.0
                line.x_qty_consumed = 0.0
                continue

            if not line.dossier_id:
                line.x_remaining_qty = line.volume
                line.x_qty_reserved = 0.0
                line.x_qty_available = line.volume
                line.x_qty_consumed = 0.0
                continue

            # Lọc các dòng sổ cái liên quan đến loài gỗ của dòng này
            ledgers = line.dossier_id.ledger_ids.filtered(lambda l: l.species_id == line.species_id)
            done_ledgers = ledgers.filtered(lambda l: l.state == 'done')
            draft_ledgers = ledgers.filtered(lambda l: l.state == 'draft')

            # Để an toàn cho trường hợp có nhiều dòng cùng loài gỗ,
            # ta tính tổng thể tích ban đầu của loài gỗ này trong toàn bộ hồ sơ
            same_species_lines = line.dossier_id.line_ids.filtered(
                lambda l: l.species_id == line.species_id and l.wood_type == 'wood'
            )
            total_initial_vol = sum(same_species_lines.mapped('volume'))

            # Tính tổng tồn kho của loài gỗ này
            species_remaining = total_initial_vol + sum(done_ledgers.mapped('actual_qty'))
            species_reserved = abs(sum(draft_ledgers.mapped('actual_qty')))
            
            # Phân bổ tỷ lệ thuận theo volume của dòng hiện tại so với tổng volume của loài gỗ đó
            if total_initial_vol > 0:
                ratio = line.volume / total_initial_vol
                line.x_remaining_qty = round(species_remaining * ratio, 2)
                line.x_qty_reserved = round(species_reserved * ratio, 2)
                line.x_qty_available = round(line.x_remaining_qty - line.x_qty_reserved, 2)
                line.x_qty_consumed = round(max(0.0, line.volume - line.x_remaining_qty), 2)
            else:
                line.x_remaining_qty = 0.0
                line.x_qty_reserved = 0.0
                line.x_qty_available = 0.0
                line.x_qty_consumed = 0.0

    @api.onchange('species_id')
    def _onchange_species_id(self):
        if self.species_id:
            if self.species_id.wood_type == 'firewood':
                # Củi không cần đường kính/chiều cao — xoá sạch và chỉ lấy giá
                self.grade_id = False
                self.diameter_min = 0
                self.diameter_max = 0
                self.height = 0.0
                self.quantity = 0
                self.volume = 0
                # Lấy giá mặc định từ grade đầu tiên nếu có
                first_grade = self.env['dl.wood.species.grade'].search(
                    [('species_id', '=', self.species_id.id)], limit=1
                )
                if first_grade:
                    self.price_unit = first_grade.default_price
            else:
                first_grade = self.env['dl.wood.species.grade'].search(
                    [('species_id', '=', self.species_id.id)], limit=1
                )
                if first_grade:
                    self.grade_id = first_grade
                    # Gán luôn các giá trị định mức
                    self.diameter_min = first_grade.diameter_min
                    self.diameter_max = first_grade.diameter_max
                    self.height = first_grade.height
                    self.price_unit = first_grade.default_price

    @api.onchange('grade_id')
    def _onchange_grade_id(self):
        if self.grade_id:
            self.diameter_min = self.grade_id.diameter_min
            self.diameter_max = self.grade_id.diameter_max
            self.height = self.grade_id.height
            self.price_unit = self.grade_id.default_price

    @api.onchange('volume', 'diameter_min', 'diameter_max', 'height')
    def _onchange_calculate_quantity(self):
        """
        Tự động tính số lượng dựa trên khối lượng và kích thước (chỉ áp dụng cho GỖ).
        Củi không tính số lượng theo công thức này.
        Công thức: Số lượng = Khối lượng / (Diện tích mặt cắt * Chiều cao)
        Diện tích mặt cắt = (D_tb/100)^2 * 3.14159 / 4
        """
        for line in self:
            # Bỏ qua củi — củi không tính số lượng theo đường kính/chiều cao
            if line.wood_type == 'firewood':
                continue
            if line.volume and (line.diameter_min or line.diameter_max) and line.height:
                # Tính đường kính trung bình (cm)
                d_avg = (line.diameter_min + line.diameter_max) / 2.0
                if d_avg > 0:
                    # Tính thể tích của 1 khúc gỗ (m3)
                    # Thể tích = (D/100)^2 * (Pi/4) * H
                    # Pi/4 xấp xỉ 0.785398
                    vol_per_piece = ((d_avg / 100.0) ** 2) * 0.785398 * line.height
                    
                    if vol_per_piece > 0:
                        # Tính số lượng và làm tròn
                        line.quantity = int(round(line.volume / vol_per_piece))
    diameter_min = fields.Integer(string='ĐK Min (cm)')
    diameter_max = fields.Integer(string='ĐK Max (cm)')
    diameter_display = fields.Char(string='ĐK (cm)', compute='_compute_diameter_display', help='Hiển thị dạng Min-Max')
    height = fields.Float(string='Cao (m)')
    height_display = fields.Char(string='Cao (m)', compute='_compute_height_display')
    avg_diameter = fields.Float(string='ĐK Trung bình (cm)')
    avg_height = fields.Float(string='Cao Trung bình (m)')

    @api.depends('diameter_min', 'diameter_max')
    def _compute_diameter_display(self):
        for line in self:
            if line.diameter_min or line.diameter_max:
                if line.diameter_min == line.diameter_max:
                    line.diameter_display = str(line.diameter_min)
                else:
                    line.diameter_display = f"{line.diameter_min}-{line.diameter_max}"
            else:
                line.diameter_display = ""

    @api.depends('height')
    def _compute_height_display(self):
        for line in self:
            line.height_display = f"{line.height:.1f}".replace('.', ',') if line.height else ""
    
    note = fields.Char(string='Ghi chú')
    x_woodpro_id = fields.Char(string='ID WoodPro')

    def write(self, vals):
        for rec in self:
            if rec.dossier_id.state in ('using', 'summary', 'confirmed'):
                raise UserError(_("Không thể chỉnh sửa dòng chi tiết gỗ khi Hồ sơ gỗ liên quan đang ở trạng thái '%s'.") % rec.dossier_id.state)
        return super(DlWoodDossierLine, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('dossier_id'):
                dossier = self.env['dl.wood.dossier'].browse(vals['dossier_id'])
                if dossier.state in ('using', 'summary', 'confirmed'):
                    raise UserError(_("Không thể thêm dòng chi tiết gỗ mới khi Hồ sơ gỗ liên quan đang ở trạng thái '%s'.") % dossier.state)
        return super(DlWoodDossierLine, self).create(vals_list)

    def unlink(self):
        for rec in self:
            if rec.dossier_id.state in ('using', 'summary', 'confirmed'):
                raise UserError(_("Không thể xóa dòng chi tiết gỗ khi Hồ sơ gỗ liên quan đang ở trạng thái '%s'.") % rec.dossier_id.state)
        return super(DlWoodDossierLine, self).unlink()


class DlWoodDossierAttachment(models.Model):
    _name = 'dl.wood.dossier.attachment'
    _description = 'Tệp đính kèm từ WoodPro'

    dossier_id = fields.Many2one('dl.wood.dossier', string='Hồ Sơ Gỗ', ondelete='cascade')
    name = fields.Char(string='Tên tệp', required=True)
    x_woodpro_id = fields.Char(string='WoodPro ID')
    status = fields.Char(string='Trạng thái')
    url = fields.Char(string='Link tải')
    file_type = fields.Selection([
        ('forest_exploitation', 'Phiếu thông tin khai thác'),
        ('hsg', 'Hợp đồng/Hồ sơ'),
        ('manifest', 'Bảng kê lâm sản'),
    ], string='Loại tệp')
    company_id = fields.Many2one('res.company', related='dossier_id.company_id', store=True, index=True)

    def action_download_file(self):
        self.ensure_one()
        if not self.url:
            raise UserError(_("Tệp này không có đường dẫn tải về."))
        return {
            'type': 'ir.actions.act_url',
            'url': self.url,
            'target': 'new',
        }


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def download_attachment(self):
        """Hỗ trợ tải file nhanh từ giao diện List view"""
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.id}?download=true',
            'target': 'self',
        }


class DlWoodReportVersion(models.Model):
    _name = 'dl.wood.report.version'
    _description = 'Phiên bản biểu mẫu báo cáo'
    _order = 'id desc'

    name = fields.Char(string='Tên phiên bản', required=True)
    code = fields.Char(string='Mã phiên bản', required=True, help="Ví dụ: v2025, v2026")
    active = fields.Boolean(string='Đang sử dụng', default=True)
    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company)
    template_config_ids = fields.One2many('dl.wood.report.template.config', 'version_id', string='Cấu hình mẫu tài liệu')


class DlWoodReportTemplateConfig(models.Model):
    _name = 'dl.wood.report.template.config'
    _description = 'Cấu hình mẫu tài liệu'
    _order = 'sequence, id'

    version_id = fields.Many2one('dl.wood.report.version', string='Phiên bản', ondelete='cascade')
    sequence = fields.Integer(string='STT', default=10)
    name = fields.Char(string='Tên tài liệu', required=True)
    template_key = fields.Char(string='Mã kỹ thuật', compute='_compute_template_key', store=True, readonly=False, help="Dùng để định danh mẫu trong code")
    is_enabled = fields.Boolean(string='Sử dụng', default=True)
    category = fields.Selection([
        ('exploitation', 'Hồ sơ khai thác'),
        ('logistics', 'Hồ sơ vận chuyển/Bàn giao')
    ], string='Phân loại', default='exploitation')
    template_file = fields.Binary(string='File mẫu (.docx)')
    template_filename = fields.Char(string='Tên file mẫu')
    dl_upload_date = fields.Datetime(string='Ngày tải lên', readonly=True)

    def _sanitize_docx_template(self, file_bytes):
        """
        Tự động làm sạch split-runs cho {%tr và phân tách các hàng bảng
        bị gộp {%tr for %} và {%tr endfor %} thành 3 hàng chuẩn theo docxtpl.
        """
        import io
        import re
        import zipfile

        def extract_text_from_xml_runs(xml_fragment):
            texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', xml_fragment)
            return ''.join(texts)

        def fix_tr_tags_in_xml(xml_str):
            # 1. Gộp {% + tr bị tách
            pattern_split_pct_tr = re.compile(
                r'\{%</w:t>'
                r'</w:r>'
                r'(?:<w:r[^>]*>)'
                r'<w:t>'
                r'tr'
                r'</w:t>'
                r'</w:r>'
            )
            new_xml = pattern_split_pct_tr.sub(lambda m: '{%tr', xml_str)
            # Chuẩn hóa khoảng trắng
            new_xml = re.sub(r'\{%tr\s+', '{%tr ', new_xml)
            
            # 2. Gộp XML runs sau {%tr
            def replace_tr_block(m):
                full_match = m.group(0)
                xml_inner = full_match[4:]
                raw_text = extract_text_from_xml_runs(xml_inner)
                if not raw_text:
                    raw_text = re.sub(r'<[^>]+>', '', xml_inner)
                clean_text = raw_text.strip()
                return '{%tr ' + clean_text
                
            pattern_split_block = re.compile(
                r'\{%tr'
                r'(?![\s])'
                r'(?:[^%]|%(?!\}))*'
                r'%\}'
            )
            new_xml = pattern_split_block.sub(replace_tr_block, new_xml)
            return new_xml

        def split_combined_table_rows(xml_str):
            tr_pattern = re.compile(r'<w:tr\b[^>]*>.*?</w:tr>', re.DOTALL)
            fixed_count = 0
            new_xml_parts = []
            last_idx = 0
            
            for m in tr_pattern.finditer(xml_str):
                tr_content = m.group(0)
                if '{%tr for' in tr_content and '{%tr endfor' in tr_content:
                    tr_attrs = re.match(r'<w:tr\b([^>]*)>', tr_content).group(0)
                    tc_pattern = re.compile(r'<w:tc\b[^>]*>.*?</w:tc>', re.DOTALL)
                    tcs = tc_pattern.findall(tr_content)
                    if len(tcs) >= 2:
                        cell_for = tcs[0]
                        cell_endfor = tcs[-1]
                        
                        # Trích xuất tag {%tr for ... %} một cách tổng quát
                        for_tag_match = re.search(r'\{%tr\s+for\s+[^%]+%\}', cell_for)
                        endfor_tag_match = re.search(r'\{%tr\s+endfor\s*%\}', cell_endfor)
                        
                        if for_tag_match and endfor_tag_match:
                            for_tag = for_tag_match.group(0)
                            endfor_tag = endfor_tag_match.group(0)
                            
                            row_for = f"{tr_attrs}{cell_for}</w:tr>"
                            row_endfor = f"{tr_attrs}{cell_endfor}</w:tr>"
                            
                            cell_for_clean = cell_for.replace(for_tag, '')
                            cell_endfor_clean = cell_endfor.replace(endfor_tag, '')
                            
                            row_data_cells = [cell_for_clean] + tcs[1:-1] + [cell_endfor_clean]
                            row_data = f"{tr_attrs}{''.join(row_data_cells)}</w:tr>"
                            
                            three_rows = f"{row_for}\n{row_data}\n{row_endfor}"
                            
                            new_xml_parts.append(xml_str[last_idx:m.start()])
                            new_xml_parts.append(three_rows)
                            last_idx = m.end()
                            fixed_count += 1
                            continue
            if fixed_count > 0:
                new_xml_parts.append(xml_str[last_idx:])
                return ''.join(new_xml_parts)
            else:
                return xml_str

        output = io.BytesIO()
        fixed = False
        
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes), 'r') as zin:
                with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zout:
                    for item in zin.infolist():
                        data = zin.read(item.filename)
                        if item.filename.endswith('.xml') and (item.filename.startswith('word/') or item.filename == '[Content_Types].xml'):
                            xml_str = data.decode('utf-8', errors='ignore')
                            # 1. Sửa lỗi split runs cho {%tr
                            xml_fixed = fix_tr_tags_in_xml(xml_str)
                            # 2. Phân tách hàng bảng bị gộp
                            xml_fixed = split_combined_table_rows(xml_fixed)
                            if xml_fixed != xml_str:
                                fixed = True
                                data = xml_fixed.encode('utf-8')
                        zout.writestr(item, data)
            if fixed:
                return output.getvalue()
        except Exception as zip_err:
            _logger.error("Lỗi khi giải nén/làm sạch file docx mẫu: %s", zip_err)
            
        return file_bytes

    @api.model_create_multi
    def create(self, vals_list):
        import base64
        for vals in vals_list:
            if 'template_file' in vals and vals['template_file']:
                vals['dl_upload_date'] = fields.Datetime.now()
                try:
                    file_bytes = base64.b64decode(vals['template_file'])
                    sanitized = self._sanitize_docx_template(file_bytes)
                    if sanitized != file_bytes:
                        vals['template_file'] = base64.b64encode(sanitized)
                        _logger.info("Tự động tối ưu hóa và làm sạch file mẫu thành công khi tạo mới.")
                except Exception as e:
                    _logger.warning("Lỗi tự động làm sạch file mẫu khi tạo mới: %s", e)
        return super().create(vals_list)

    def write(self, vals):
        import base64
        if 'template_file' in vals:
            if vals.get('template_file'):
                vals['dl_upload_date'] = fields.Datetime.now()
                try:
                    file_bytes = base64.b64decode(vals['template_file'])
                    sanitized = self._sanitize_docx_template(file_bytes)
                    if sanitized != file_bytes:
                        vals['template_file'] = base64.b64encode(sanitized)
                        _logger.info("Tự động tối ưu hóa và làm sạch file mẫu thành công khi cập nhật.")
                except Exception as e:
                    _logger.warning("Lỗi tự động làm sạch file mẫu khi cập nhật: %s", e)
            else:
                vals['dl_upload_date'] = False
        return super().write(vals)

    @api.depends('name')
    def _compute_template_key(self):
        for rec in self:
            # Chỉ tự động sinh mã kỹ thuật nếu mã kỹ thuật đang trống và có tên tài liệu
            if rec.name and not rec.template_key:
                raw_name = rec.name
                if '. ' in raw_name:
                    raw_name = raw_name.split('. ', 1)[1]
                
                clean = no_accent_vietnamese(raw_name).lower()
                rec.template_key = clean
            elif not rec.name:
                rec.template_key = False
