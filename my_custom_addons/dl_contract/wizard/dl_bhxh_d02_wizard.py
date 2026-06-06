# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import io
import base64
from datetime import datetime, date
import openpyxl

class DlBhxhD02Wizard(models.TransientModel):
    _name = 'dl.bhxh.d02.wizard'
    _description = 'Wizard xuất báo cáo Báo tăng BHXH (Mẫu D02-LT)'

    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company)
    date_from = fields.Date(string='Từ ngày', required=True)
    date_to = fields.Date(string='Đến ngày', required=True)
    
    file_data = fields.Binary(string='File báo cáo', readonly=True)
    file_name = fields.Char(string='Tên file', readonly=True)
    state = fields.Selection([
        ('choose', 'Chọn tham số'),
        ('done', 'Hoàn tất')
    ], default='choose')

    @api.model
    def default_get(self, fields_list):
        res = super(DlBhxhD02Wizard, self).default_get(fields_list)
        today = date.today()
        # Mặc định gợi ý chu kỳ báo tăng
        if today.day <= 15:
            date_from = today.replace(day=1)
            date_to = today.replace(day=15)
        else:
            # Tính ngày cuối tháng
            import calendar
            last_day = calendar.monthrange(today.year, today.month)[1]
            date_from = today.replace(day=16)
            date_to = today.replace(day=last_day)
        
        if 'date_from' in fields_list and not res.get('date_from'):
            res['date_from'] = date_from
        if 'date_to' in fields_list and not res.get('date_to'):
            res['date_to'] = date_to
            
        return res

    def action_export_excel(self):
        self.ensure_one()
        
        # 1. Tìm các hợp đồng lao động thỏa mãn
        contract_domain = [
            ('company_id', '=', self.company_id.id),
            ('state', 'in', ('active', 'draft')),
            ('date_start', '>=', self.date_from),
            ('date_start', '<=', self.date_to),
            ('scan_file', '!=', False)
        ]
        contracts = self.env['dl.contract'].search(contract_domain, order='date_start asc, id asc')
        
        if not contracts:
            raise UserError(_('Không tìm thấy nhân viên nào có hợp đồng hiệu lực và có bản scan hợp đồng trong khoảng thời gian từ %s đến %s.') % (
                self.date_from.strftime('%d/%m/%Y'),
                self.date_to.strftime('%d/%m/%Y')
            ))

        # 2. Đọc file template
        template_path = '/Users/sonzai/dev/odoo 19/odoo/my_custom_addons/dl_contract/static/templates/bhxh/FileMau-D02LT_v2.xlsx'
        try:
            wb = openpyxl.load_workbook(template_path, data_only=False)
        except Exception as e:
            raise UserError(_('Không thể mở file template tại %s. Chi tiết lỗi: %s') % (template_path, str(e)))

        ws_dl = wb['DuLieu']
        ws_pl = wb['PL TV HGĐ']

        # Dữ liệu xuất sheet DuLieu bắt đầu từ dòng 5
        dl_row = 5
        # Dữ liệu xuất sheet PL TV HGĐ bắt đầu từ dòng 6
        pl_row = 6
        stt = 1

        for contract in contracts:
            employee = contract.employee_id
            
            # Phân loại Tăng mới (TM) / Tăng lại (TL)
            phuong_an = 'TM-Tăng mới' # Mặc định
            if contract.previous_contract_id:
                prev_contract = contract.previous_contract_id
                if prev_contract.date_end:
                    delta = (contract.date_start - prev_contract.date_end).days
                    if delta > 1:
                        phuong_an = 'ON-Đi làm lại'
                    else:
                        # Kiểm tra xem hợp đồng trước đó có phải thử việc
                        prev_type = prev_contract.contract_type_id
                        prev_name = (prev_type.name or '').lower()
                        prev_code = (prev_type.code or '').lower()
                        if 'thử việc' in prev_name or 'trial' in prev_name or 'probation' in prev_name or 'trial' in prev_code:
                            phuong_an = 'TM-Tăng mới'
                        else:
                            # Nếu là gia hạn HĐ chính thức nối tiếp thì có thể không cần báo tăng,
                            # nhưng vì đã lọc vào danh sách nên ta coi là Tăng mới (hoặc giữ nguyên mặc định TM)
                            phuong_an = 'TM-Tăng mới'
                else:
                    phuong_an = 'TM-Tăng mới'
            
            # Format ngày tháng năm sinh
            dob_str = ''
            if employee.birthday:
                dob_str = employee.birthday.strftime('%d/%m/%Y')
                
            # Giới tính
            gender_val = ''
            if employee.sex == 'male':
                gender_val = '1'
            elif employee.sex == 'female':
                gender_val = '0'

            # Dân tộc
            ethnic_val = ''
            # Mặc định Odoo hr.employee không có sẵn Selection dân tộc từ core, 
            # nhưng trong dl_contract đã tích hợp hoặc lưu trữ dưới dạng selection hoặc text.
            # Lấy trường dân tộc của nhân viên (thường được lưu trong dl_ethnic_name như model gia đình)
            if hasattr(employee, 'dl_ethnic_name') and employee.dl_ethnic_name:
                # Tìm nhãn hiển thị của selection
                ethnic_dict = dict(employee.fields_get(allfields=['dl_ethnic_name'])['dl_ethnic_name']['selection'])
                ethnic_val = ethnic_dict.get(employee.dl_ethnic_name, '')
            if not ethnic_val:
                # Thử lấy từ trường dân tộc của Odoo nếu có, hoặc để mặc định "Kinh"
                ethnic_val = 'Kinh'

            # Quốc tịch
            country_val = 'VIET NAM'
            if employee.country_id:
                # Chuyển đổi sang viết hoa không dấu
                import unicodedata
                normalized = unicodedata.normalize('NFKD', employee.country_id.name or '').encode('ascii', 'ignore').decode('utf-8')
                country_val = normalized.upper()
                if 'VIET NAM' in country_val:
                    country_val = 'VIET NAM'

            # Tỉnh/Xã Khai sinh
            birth_province = ''
            birth_ward = ''
            # Tìm trong tab thành viên gia đình xem có thành viên là bản thân nhân viên hoặc lấy từ thông tin nhân viên.
            # Nếu nhân viên có khai báo Tỉnh/Xã khai sinh trên form nhân viên (ở đây ta ưu tiên lấy từ thông tin chủ hộ nếu có)
            
            # Thông tin chủ hộ từ tab thành viên gia đình
            head_member = employee.dl_family_member_ids.filtered(lambda m: m.dl_relation == '00')
            
            head_name = ''
            head_cccd = ''
            head_phone = ''
            head_province_name = ''
            head_ward_name = ''
            head_address = ''
            
            if head_member:
                head = head_member[0]
                head_name = head.dl_name or ''
                head_cccd = head.dl_cccd or ''
                head_phone = head.dl_phone or ''
                head_address = head.dl_birth_address or ''
                
                # Tìm tỉnh khai sinh của chủ hộ
                prov_state = head.dl_birth_state_id
                if prov_state:
                    head_province_name = prov_state.x_gso_name or prov_state.name or ''
                elif head.dl_birth_province:
                    prov_state = self.env['res.country.state'].search([
                        ('country_id.code', '=', 'VN'),
                        '|', ('name', 'ilike', head.dl_birth_province), ('x_gso_name', 'ilike', head.dl_birth_province)
                    ], limit=1)
                    if prov_state:
                        head_province_name = prov_state.x_gso_name or prov_state.name or ''
                
                # Tìm xã khai sinh của chủ hộ
                if head.dl_birth_ward_id:
                    head_ward_name = head.dl_birth_ward_id.name or ''
                elif head.dl_birth_ward:
                    # Tìm xã trong tỉnh
                    ward_domain = [('name', 'ilike', head.dl_birth_ward)]
                    if prov_state:
                        ward_domain.append(('state_id', '=', prov_state.id))
                    ward_rec = self.env['res.country.ward'].search(ward_domain, limit=1)
                    if ward_rec:
                        head_ward_name = ward_rec.name or ''
                    else:
                        head_ward_name = head.dl_birth_ward

            # Lấy thông tin khai sinh trực tiếp của nhân viên từ tab Cá nhân
            birth_province = employee.x_birth_state_id.x_gso_name or employee.x_birth_state_id.name or ''
            birth_ward = employee.x_birth_ward_id.name or ''
            birth_address = employee.x_birth_address or ''

            # Fallback lấy từ dòng tự khai trong tab gia đình hoặc chủ hộ nếu thông tin trực tiếp bị trống
            if not birth_province or not birth_ward:
                self_member = employee.dl_family_member_ids.filtered(lambda m: m.dl_relation in ('00', '99') and m.dl_name == employee.name)
                if self_member:
                    self_m = self_member[0]
                    if not birth_province and self_m.dl_birth_province:
                        prov_state = self.env['res.country.state'].search([
                            ('country_id.code', '=', 'VN'),
                            '|', ('name', 'ilike', self_m.dl_birth_province), ('x_gso_name', 'ilike', self_m.dl_birth_province)
                        ], limit=1)
                        if prov_state:
                            birth_province = prov_state.x_gso_name or prov_state.name or ''
                    if not birth_ward and self_m.dl_birth_ward:
                        ward_domain = [('name', 'ilike', self_m.dl_birth_ward)]
                        if 'prov_state' in locals() and prov_state:
                            ward_domain.append(('state_id', '=', prov_state.id))
                        ward_rec = self.env['res.country.ward'].search(ward_domain, limit=1)
                        if ward_rec:
                            birth_ward = ward_rec.name or ''
                        else:
                            birth_ward = self_m.dl_birth_ward

            if not birth_province:
                birth_province = head_province_name
            if not birth_ward:
                birth_ward = head_ward_name
            if not birth_address:
                # Nếu địa chỉ chi tiết trống, lấy private_street hoặc fallback là birth_ward
                birth_address = employee.private_street or birth_ward

            # Mức lương & Phụ cấp
            wage_val = contract.wage or 0
            allowance_val = contract.allowance or 0
            
            # Thời gian HĐ
            start_date_str = contract.date_start.strftime('%d/%m/%Y') if contract.date_start else ''
            end_date_str = contract.date_end.strftime('%d/%m/%Y') if contract.date_end else ''
            tu_thang_str = contract.date_start.strftime('%m/%Y') if contract.date_start else ''
            den_thang_str = contract.date_end.strftime('%m/%Y') if contract.date_end else ''

            # Thông tin KCB
            kcb_province = ''
            kcb_hospital = employee.x_kcb_hospital or ''
            if employee.x_kcb_state_id:
                kcb_province = employee.x_kcb_state_id.x_gso_name or ''

            # Ghi thông tin vào sheet DuLieu
            ws_dl.cell(row=dl_row, column=1, value=stt) # STT
            ws_dl.cell(row=dl_row, column=2, value=employee.name) # Họ tên
            ws_dl.cell(row=dl_row, column=3, value=employee.ssnid or '') # Mã số BHXH
            ws_dl.cell(row=dl_row, column=4, value='Tăng lao động') # Tên Loại hồ sơ
            # Cột E: LoạiHoSo (Công thức giữ nguyên)
            ws_dl.cell(row=dl_row, column=6, value=phuong_an) # Phương án
            # Cột G: Phương án ID (Công thức giữ nguyên)
            ws_dl.cell(row=dl_row, column=8, value='0') # Chỉ có năm sinh? (Không -> 0)
            ws_dl.cell(row=dl_row, column=9, value=dob_str) # Ngày sinh
            ws_dl.cell(row=dl_row, column=10, value=gender_val) # Giới tính
            ws_dl.cell(row=dl_row, column=11, value=employee.identification_id or '') # Số CCCD
            ws_dl.cell(row=dl_row, column=12, value=contract.job_title or '') # Chức vụ
            ws_dl.cell(row=dl_row, column=13, value=contract.department_id.name or '') # Phòng ban
            ws_dl.cell(row=dl_row, column=14, value='FALSE') # Cột N
            ws_dl.cell(row=dl_row, column=15, value=contract.company_id.name or '') # Nơi làm việc (Tên công ty)
            ws_dl.cell(row=dl_row, column=16, value=wage_val) # Tiền lương
            ws_dl.cell(row=dl_row, column=17, value=allowance_val) # Phụ cấp lương
            ws_dl.cell(row=dl_row, column=22, value=tu_thang_str) # Từ tháng
            ws_dl.cell(row=dl_row, column=23, value=tu_thang_str) # Đến tháng (Tháng bắt đầu ký HĐ)
            
            # Tính ngày ký hợp đồng = ngày hiệu lực - 2 ngày
            sign_date_str = ''
            if contract.date_start:
                from datetime import timedelta
                sign_date = contract.date_start - timedelta(days=2)
                sign_date_str = sign_date.strftime('%d/%m/%Y')
            ws_dl.cell(row=dl_row, column=24, value=f"{contract.name or ''} ký ngày {sign_date_str} hiệu lực ngày {start_date_str}" if contract.date_start else '') # Cột X (Ghi chú)

            ws_dl.cell(row=dl_row, column=25, value='TRUE') # Đã có sổ? Mặc định TRUE
            ws_dl.cell(row=dl_row, column=27, value=32) # Cột AA
            ws_dl.cell(row=dl_row, column=30, value='FALSE') # Có giảm chết? FALSE
            ws_dl.cell(row=dl_row, column=32, value='FALSE') # Cột AF
            ws_dl.cell(row=dl_row, column=36, value='1' if contract.contract_type_id.duration_type == 'fixed' else '0') # Loại HĐLĐ (0: vô thời hạn, 1: có thời hạn)
            ws_dl.cell(row=dl_row, column=37, value=start_date_str) # Từ ngày HĐLĐ
            ws_dl.cell(row=dl_row, column=38, value=end_date_str) # Đến ngày HĐLĐ
            ws_dl.cell(row=dl_row, column=41, value='TRUE') # Xuất TK01? TRUE
            ws_dl.cell(row=dl_row, column=42, value=country_val) # Quốc tịch
            # Cột AQ: Quốc tịch ID (Công thức giữ nguyên)
            ws_dl.cell(row=dl_row, column=44, value=ethnic_val) # Dân tộc
            # Cột AS: Dân tộc ID (Công thức giữ nguyên)
            ws_dl.cell(row=dl_row, column=46, value=employee.work_phone or employee.mobile_phone or '') # Điện thoại liên hệ
            ws_dl.cell(row=dl_row, column=47, value=employee.work_email or '') # Email
            ws_dl.cell(row=dl_row, column=48, value=birth_province) # Khai sinh Tỉnh
            # Cột AW: Khai sinh Tỉnh ID (Công thức giữ nguyên)
            ws_dl.cell(row=dl_row, column=50, value=birth_ward) # Khai sinh Xã
            # Cột AY: Khai sinh Xã ID (Công thức giữ nguyên)
            ws_dl.cell(row=dl_row, column=52, value=birth_address) # Địa chỉ khai sinh chi tiết
            
            # KCB
            ws_dl.cell(row=dl_row, column=58, value=kcb_province) # Tỉnh KCB
            # Cột BG: Tỉnh KCB ID (Công thức giữ nguyên)
            ws_dl.cell(row=dl_row, column=60, value=kcb_hospital) # Bệnh viện KCB
            # Cột BI: Bệnh viện KCB ID (Công thức giữ nguyên)
            ws_dl.cell(row=dl_row, column=62, value='FALSE') # Cột BJ

            # Nơi nhận bản giấy (Mặc định lấy như khai sinh hoặc để trống) - Để trống theo yêu cầu

            # Hộ gia đình & Chủ hộ (Cột BU đến CK)
            ws_dl.cell(row=dl_row, column=73, value=employee.x_household_code or '') # Mã hộ gia đình (cột BU)
            ws_dl.cell(row=dl_row, column=74, value=head_name) # Họ tên chủ hộ (cột BV)
            ws_dl.cell(row=dl_row, column=75, value=head_cccd) # CCCD chủ hộ (cột BW)
            ws_dl.cell(row=dl_row, column=76, value=head_phone) # Điện thoại chủ hộ (cột BX)

            # ws_dl.cell(row=dl_row, column=77, value='01') # Loại giấy tờ ID (cột BY, mặc định 01 - CCCD)
            # ws_dl.cell(row=dl_row, column=78, value=head_cccd) # Số giấy tờ (cột BZ)
            
            # Thường trú chủ hộ
            ws_dl.cell(row=dl_row, column=79, value=head_province_name) # ChuHoTinh (cột CA)
            # Cột CB: ChuHoTinhId (Công thức giữ nguyên)
            ws_dl.cell(row=dl_row, column=81, value=head_ward_name) # ChuHoXa (cột CC)
            # Cột CD: ChuHoXaId (Công thức giữ nguyên)
            ws_dl.cell(row=dl_row, column=83, value=head_address) # DiaChiHoKhau (cột CE)
            
            # Tạm trú chủ hộ (ghi giống thường trú)
            ws_dl.cell(row=dl_row, column=84, value=head_province_name) # ChuHoThuongTruTinh (cột CF)
            # Cột CG: ChuHoThuongTruTinhId (Công thức giữ nguyên)
            ws_dl.cell(row=dl_row, column=86, value=head_ward_name) # ChuHoThuongTruXa (cột CH)
            # Cột CI: ChuHoThuongTruXaId (Công thức giữ nguyên)
            ws_dl.cell(row=dl_row, column=88, value=head_address) # DiaChiThuongTruChuHo (cột CJ)
            ws_dl.cell(row=dl_row, column=89, value=employee.x_household_code or '') # Mã số hộ gia đình (cột CK)

            # 3. Ghi thông tin thành viên gia đình vào sheet PL TV HGĐ
            for member in employee.dl_family_member_ids:
                # Họ tên thành viên
                ws_pl.cell(row=pl_row, column=1, value=stt) # Cột A: STT trên D02-LT (khớp với nhân viên)
                ws_pl.cell(row=pl_row, column=2, value=member.dl_name) # Cột B: Họ và tên
                ws_pl.cell(row=pl_row, column=3, value=member.dl_ssnid or '') # Cột C: Mã số BHXH thành viên (nếu có)
                ws_pl.cell(row=pl_row, column=4, value='0') # Cột D: Loại ngày sinh (0: đầy đủ ngày tháng)
                
                member_dob = ''
                if member.dl_birthday:
                    member_dob = member.dl_birthday.strftime('%d/%m/%Y')
                ws_pl.cell(row=pl_row, column=5, value=member_dob) # Cột E: Ngày sinh
                
                member_gender = ''
                if member.dl_gender == 'male':
                    member_gender = '1'
                elif member.dl_gender == 'female':
                    member_gender = '2'
                ws_pl.cell(row=pl_row, column=6, value=member_gender) # Cột F: Giới tính
                
                # Quốc tịch thành viên
                ws_pl.cell(row=pl_row, column=7, value='VIET NAM') # Cột G: Tên quốc tịch
                # Cột H: Quốc tịch ID (Công thức giữ nguyên)
                
                # Dân tộc thành viên
                m_ethnic_val = 'Kinh'
                if member.dl_ethnic_name:
                    m_ethnic_dict = dict(member.fields_get(allfields=['dl_ethnic_name'])['dl_ethnic_name']['selection'])
                    m_ethnic_val = m_ethnic_dict.get(member.dl_ethnic_name, 'Kinh')
                ws_pl.cell(row=pl_row, column=9, value=m_ethnic_val) # Cột I: Tên dân tộc
                # Cột J: Dân tộc ID (Công thức giữ nguyên)
                
                ws_pl.cell(row=pl_row, column=11, value=member.dl_cccd or '') # Cột K: Số CCCD
                
                # Địa chỉ khai sinh thành viên
                m_prov_rec = member.dl_birth_state_id
                m_prov_name = ''
                if m_prov_rec:
                    m_prov_name = m_prov_rec.x_gso_name or m_prov_rec.name or ''
                elif member.dl_birth_province:
                    m_prov_rec = self.env['res.country.state'].search([
                        ('country_id.code', '=', 'VN'),
                        '|', ('name', 'ilike', member.dl_birth_province), ('x_gso_name', 'ilike', member.dl_birth_province)
                    ], limit=1)
                    if m_prov_rec:
                        m_prov_name = m_prov_rec.x_gso_name or m_prov_rec.name or ''
                ws_pl.cell(row=pl_row, column=12, value=m_prov_name) # Cột L: Tỉnh khai sinh
                # Cột M: Mã tỉnh (Công thức giữ nguyên)
                
                m_ward_name = ''
                if member.dl_birth_ward_id:
                    m_ward_name = member.dl_birth_ward_id.name or ''
                elif member.dl_birth_ward:
                    m_ward_domain = [('name', 'ilike', member.dl_birth_ward)]
                    if m_prov_rec:
                        m_ward_domain.append(('state_id', '=', m_prov_rec.id))
                    m_ward_rec = self.env['res.country.ward'].search(m_ward_domain, limit=1)
                    if m_ward_rec:
                        m_ward_name = m_ward_rec.name or ''
                    else:
                        m_ward_name = member.dl_birth_ward
                ws_pl.cell(row=pl_row, column=14, value=m_ward_name) # Cột N: Phường/Xã khai sinh
                # Cột O: Mã xã (Công thức giữ nguyên)
                
                ws_pl.cell(row=pl_row, column=16, value=member.dl_birth_address or '') # Cột P: Địa chỉ chi tiết
                
                # Mối quan hệ
                relation_val = 'Khác'
                if member.dl_relation:
                    relation_dict = dict(member.fields_get(allfields=['dl_relation'])['dl_relation']['selection'])
                    relation_val = relation_dict.get(member.dl_relation, 'Khác')
                ws_pl.cell(row=pl_row, column=17, value=relation_val) # Cột Q: Mối quan hệ
                # Cột R: Mã MQH (Công thức giữ nguyên)
                
                pl_row += 1
            
            dl_row += 1
            stt += 1

        # 4. Xuất file Excel dưới dạng base64
        fp = io.BytesIO()
        wb.save(fp)
        fp.seek(0)
        file_data = base64.b64encode(fp.read())
        fp.close()

        # Tạo tên file
        file_name = 'BaoTang_BHXH_D02LT_%s_den_%s.xlsx' % (
            self.date_from.strftime('%d%m%Y'),
            self.date_to.strftime('%d%m%Y')
        )

        self.write({
            'file_data': file_data,
            'file_name': file_name,
            'state': 'done'
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dl.bhxh.d02.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
