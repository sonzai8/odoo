# -*- coding: utf-8 -*-
from odoo.tests import common
from odoo.exceptions import UserError
from datetime import date, timedelta
import base64
import openpyxl
import io

class TestDlBhxhD02(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestDlBhxhD02, cls).setUpClass()
        cls.company = cls.env.company

        # Thêm cấu hình KCB mặc định cho công ty
        cls.kcb_state = cls.env['res.country.state'].search([('country_id.code', '=', 'VN')], limit=1)
        cls.company.write({
            'x_kcb_state_id': cls.kcb_state.id,
            'x_kcb_hospital': 'Bệnh viện đa khoa Bắc Ninh Test',
        })

        # 1. Tạo loại hợp đồng
        cls.contract_type_cth = cls.env['dl.contract.type'].create({
            'name': 'Hợp đồng xác định thời hạn',
            'code': 'CTH_TEST',
            'duration_type': 'fixed',
            'company_id': cls.company.id,
        })
        cls.contract_type_trial = cls.env['dl.contract.type'].create({
            'name': 'Hợp đồng thử việc',
            'code': 'TRIAL_TEST',
            'duration_type': 'fixed',
            'company_id': cls.company.id,
        })

        # 2. Tạo Phòng ban
        cls.dept = cls.env['hr.department'].create({
            'name': 'Phòng Kỹ Thuật Test',
            'company_id': cls.company.id,
        })

        # 2.5 Tạo Xã khai sinh test
        cls.birth_ward = cls.env['res.country.ward'].create({
            'name': 'Xã Khai Sinh Test',
            'state_id': cls.kcb_state.id,
            'x_gso_code': '00001',
        })

        # 3. Tạo nhân viên A (Tăng mới)
        cls.employee_a = cls.env['hr.employee'].create({
            'name': 'Nguyễn Văn A Test',
            'company_id': cls.company.id,
            'sex': 'male',
            'ssnid': '1234567890',
            'identification_id': '030203001111',
            'x_household_code': 'HGD001',
            'x_birth_state_id': cls.kcb_state.id,
            'x_birth_ward_id': cls.birth_ward.id,
            'x_birth_address': 'Số 123 Đường Khai Sinh',
        })
        
        # Thêm thành viên gia đình cho A (Chủ hộ là chính A)
        cls.env['dl.employee.family.member'].create({
            'employee_id': cls.employee_a.id,
            'dl_name': 'Nguyễn Văn A Test',
            'dl_birthday': date(1990, 1, 1),
            'dl_gender': 'male',
            'dl_cccd': '030203001111',
            'dl_ssnid': 'SSN_MEMBER_A',
            'dl_phone': '0987654321',
            'dl_birth_state_id': cls.kcb_state.id,
            'dl_birth_ward_id': cls.birth_ward.id,
            'dl_relation': '00', # Chủ hộ
        })
        # Thêm 1 thành viên gia đình khác (Vợ)
        cls.env['dl.employee.family.member'].create({
            'employee_id': cls.employee_a.id,
            'dl_name': 'Trần Thị B Test',
            'dl_birthday': date(1992, 2, 2),
            'dl_gender': 'female',
            'dl_cccd': '030203002222',
            'dl_ssnid': 'SSN_MEMBER_B',
            'dl_birth_state_id': cls.kcb_state.id,
            'dl_birth_ward_id': cls.birth_ward.id,
            'dl_relation': '01', # Vợ
        })

        # 4. Tạo nhân viên B (Tăng lại)
        cls.employee_b = cls.env['hr.employee'].create({
            'name': 'Lê Văn B Test',
            'company_id': cls.company.id,
            'sex': 'male',
            'ssnid': '0987654321',
            'identification_id': '030203003333',
        })

        # Giả lập lịch sử file scan PDF
        cls.dummy_pdf = base64.b64encode(b'%PDF-1.4 dummy content')

    def test_bhxh_d02_export_logic(self):
        # Kiểm tra logic KCB mặc định tự động lấy từ Công ty sang Nhân viên
        self.assertEqual(self.employee_a.x_kcb_state_id, self.kcb_state)
        self.assertEqual(self.employee_a.x_kcb_hospital, 'Bệnh viện đa khoa Bắc Ninh Test')

        # Tạo hợp đồng cho nhân viên A (Tăng mới - có file scan)
        contract_a = self.env['dl.contract'].create({
            'name': 'HĐLĐ Nguyễn Văn A',
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_cth.id,
            'date_start': date(2026, 6, 1),
            'date_end': date(2027, 6, 1),
            'wage': 8000000.0,
            'state': 'active',
            'scan_file': self.dummy_pdf,
            'scan_filename': 'contract_a.pdf',
            'company_id': self.company.id,
        })

        # Tạo hợp đồng cũ đã chấm dứt cho nhân viên B
        contract_b_old = self.env['dl.contract'].create({
            'name': 'HĐLĐ Lê Văn B Cũ',
            'employee_id': self.employee_b.id,
            'contract_type_id': self.contract_type_cth.id,
            'date_start': date(2025, 1, 1),
            'date_end': date(2025, 12, 31),
            'wage': 7000000.0,
            'state': 'terminated',
            'company_id': self.company.id,
        })

        # Tạo hợp đồng mới cho nhân viên B (Tăng lại - có file scan)
        contract_b_new = self.env['dl.contract'].create({
            'name': 'HĐLĐ Lê Văn B Mới',
            'employee_id': self.employee_b.id,
            'contract_type_id': self.contract_type_cth.id,
            'date_start': date(2026, 6, 10),
            'date_end': date(2027, 6, 10),
            'wage': 9000000.0,
            'state': 'active',
            'scan_file': self.dummy_pdf,
            'scan_filename': 'contract_b.pdf',
            'previous_contract_id': contract_b_old.id,
            'company_id': self.company.id,
        })

        # Tạo một hợp đồng C không có file scan (để test bộ lọc scan_file)
        employee_c = self.env['hr.employee'].create({
            'name': 'Trần Văn C Test',
            'company_id': self.company.id,
        })
        self.env['dl.contract'].create({
            'name': 'HĐLĐ Trần Văn C',
            'employee_id': employee_c.id,
            'contract_type_id': self.contract_type_cth.id,
            'date_start': date(2026, 6, 5),
            'wage': 7500000.0,
            'state': 'active',
            'company_id': self.company.id,
            # scan_file = False
        })

        # Khởi tạo wizard xuất báo cáo cho đợt 01/06/2026 - 15/06/2026
        wizard = self.env['dl.bhxh.d02.wizard'].create({
            'date_from': date(2026, 6, 1),
            'date_to': date(2026, 6, 15),
            'company_id': self.company.id,
        })

        # Chạy action xuất Excel
        wizard.action_export_excel()

        # Kiểm tra file đã được tạo ra hay chưa
        self.assertEqual(wizard.state, 'done')
        self.assertTrue(wizard.file_data)
        self.assertTrue(wizard.file_name.startswith('BaoTang_BHXH_D02LT_'))

        # Đọc dữ liệu từ file Excel kết quả để kiểm thử nội dung
        excel_bytes = base64.b64decode(wizard.file_data)
        wb = openpyxl.load_workbook(io.BytesIO(excel_bytes), data_only=True)
        ws_dl = wb['DuLieu']
        ws_pl = wb['PL TV HGĐ']

        # Dòng 5 phải chứa thông tin nhân viên A (do ngày bắt đầu 01/06 sớm nhất)
        self.assertEqual(ws_dl.cell(row=5, column=2).value, 'Nguyễn Văn A Test')
        self.assertEqual(ws_dl.cell(row=5, column=6).value, 'TM-Tăng mới') # TM do không có hợp đồng trước đó
        self.assertEqual(ws_dl.cell(row=5, column=15).value, self.company.name) # Tên công ty ở cột O
        self.assertEqual(ws_dl.cell(row=5, column=22).value, '06/2026') # Từ tháng
        self.assertEqual(ws_dl.cell(row=5, column=23).value, '06/2026') # Đến tháng (Tháng bắt đầu ký HĐ)
        self.assertEqual(ws_dl.cell(row=5, column=73).value, 'HGD001') # Mã hộ gia đình (BU)
        self.assertEqual(ws_dl.cell(row=5, column=74).value, 'Nguyễn Văn A Test') # Chủ hộ (BV)
        self.assertEqual(ws_dl.cell(row=5, column=76).value, '0987654321') # Điện thoại chủ hộ (BX)
        self.assertEqual(ws_dl.cell(row=5, column=27).value, 32) # Cột AA
        self.assertEqual(ws_dl.cell(row=5, column=32).value, 'FALSE') # Cột AF
        self.assertEqual(ws_dl.cell(row=5, column=62).value, 'FALSE') # Cột BJ
        self.assertEqual(ws_dl.cell(row=5, column=14).value, 'FALSE') # Cột N
        self.assertEqual(ws_dl.cell(row=5, column=36).value, '1') # Cột AJ (Loại HĐLĐ: 1 = có thời hạn)
        self.assertEqual(ws_dl.cell(row=5, column=24).value, 'HĐLĐ Nguyễn Văn A ký ngày 30/05/2026 hiệu lực ngày 01/06/2026') # Cột X: Ghi chú
        self.assertEqual(ws_dl.cell(row=5, column=48).value, self.kcb_state.x_gso_name or self.kcb_state.name) # Cột AV
        self.assertEqual(ws_dl.cell(row=5, column=50).value, 'Xã Khai Sinh Test') # Cột AX
        self.assertEqual(ws_dl.cell(row=5, column=52).value, 'Số 123 Đường Khai Sinh') # Cột AZ


        # Dòng 6 phải chứa thông tin nhân viên B (ngày bắt đầu 10/06)
        self.assertEqual(ws_dl.cell(row=6, column=2).value, 'Lê Văn B Test')
        self.assertEqual(ws_dl.cell(row=6, column=6).value, 'ON-Đi làm lại') # TL do có hợp đồng cũ cách xa
        self.assertEqual(ws_dl.cell(row=6, column=22).value, '06/2026')
        self.assertEqual(ws_dl.cell(row=6, column=23).value, '06/2026')
        self.assertEqual(ws_dl.cell(row=6, column=24).value, 'HĐLĐ Lê Văn B Mới ký ngày 08/06/2026 hiệu lực ngày 10/06/2026') # Cột X: Ghi chú

        # Nhân viên C không có scan_file nên không được xuất hiện trong list
        # Do đó dòng 7 phải trống (hoặc không chứa nhân viên C)
        self.assertNotEqual(ws_dl.cell(row=7, column=2).value, 'Trần Văn C Test')

        # Kiểm thử sheet phụ lục gia đình PL TV HGĐ
        # Dòng 6 (thành viên đầu tiên): là Nguyễn Văn A Test (Chủ hộ của A, STT nhân viên ở cột A phải là 1)
        self.assertEqual(ws_pl.cell(row=6, column=1).value, 1) # Cột A liên kết STT
        self.assertEqual(ws_pl.cell(row=6, column=2).value, 'Nguyễn Văn A Test')
        self.assertEqual(ws_pl.cell(row=6, column=3).value, 'SSN_MEMBER_A') # Cột C: BHXH

        # Dòng 7 (thành viên thứ hai): là Trần Thị B Test (Vợ của A, STT cột A vẫn phải là 1)
        self.assertEqual(ws_pl.cell(row=7, column=1).value, 1) # Cột A liên kết STT
        self.assertEqual(ws_pl.cell(row=7, column=2).value, 'Trần Thị B Test')
        self.assertEqual(ws_pl.cell(row=7, column=3).value, 'SSN_MEMBER_B') # Cột C: BHXH
        self.assertEqual(ws_pl.cell(row=6, column=12).value, self.kcb_state.x_gso_name or self.kcb_state.name) # Cột L
        self.assertEqual(ws_pl.cell(row=6, column=14).value, 'Xã Khai Sinh Test') # Cột N

    def test_kcb_standardization_action(self):
        # Tạo nhân viên mới không có KCB (giả lập bị thiếu KCB trong DB)
        employee_no_kcb = self.env['hr.employee'].create({
            'name': 'Nhân viên không KCB Test',
            'company_id': self.company.id,
        })
        employee_no_kcb.write({
            'x_kcb_state_id': False,
            'x_kcb_hospital': False,
        })

        self.assertFalse(employee_no_kcb.x_kcb_state_id)
        self.assertFalse(employee_no_kcb.x_kcb_hospital)

        # Khởi tạo wizard và thực hiện chuẩn hóa
        init_wizard = self.env['dl.contract.init.wizard'].create({})
        init_wizard.action_standardize_kcb()

        # Kiểm tra xem nhân viên đã được chuẩn hóa KCB chưa
        self.assertEqual(employee_no_kcb.x_kcb_state_id, self.kcb_state)
        self.assertEqual(employee_no_kcb.x_kcb_hospital, 'Bệnh viện đa khoa Bắc Ninh Test')

