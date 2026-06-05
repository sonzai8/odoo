# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, Form
from odoo.exceptions import ValidationError, UserError, AccessError
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import fields
import base64

class TestDlContract(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestDlContract, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # 1. Công ty mặc định
        cls.company_a = cls.env.company
        cls.company_a.x_wood_prefix = 'DL'

        # 2. Tạo công ty B để test Multi-company
        cls.company_b = cls.env['res.company'].create({
            'name': 'Company B',
            'x_wood_prefix': 'DL',
        })

        # 3. Tạo User A thuộc Company A
        cls.user_a = cls.env['res.users'].create({
            'name': 'User A',
            'login': 'usera',
            'company_id': cls.company_a.id,
            'company_ids': [(6, 0, [cls.company_a.id])],
        })
        cls.env.ref('base.group_user').user_ids = [(4, cls.user_a.id)]
        cls.env.ref('dl_contract.group_contract_manager').user_ids = [(4, cls.user_a.id)]

        # 4. Tạo User B thuộc Company B
        cls.user_b = cls.env['res.users'].create({
            'name': 'User B',
            'login': 'userb',
            'company_id': cls.company_b.id,
            'company_ids': [(6, 0, [cls.company_b.id])],
        })
        cls.env.ref('base.group_user').user_ids = [(4, cls.user_b.id)]
        cls.env.ref('dl_contract.group_contract_manager').user_ids = [(4, cls.user_b.id)]

        # Tạo Nhân viên
        cls.employee_a = cls.env['hr.employee'].create({
            'name': 'Nguyễn Văn A',
            'company_id': cls.company_a.id,
        })
        cls.employee_b = cls.env['hr.employee'].create({
            'name': 'Trần Văn B',
            'company_id': cls.company_b.id,
        })

        # Tạo loại hợp đồng
        cls.contract_type_fixed_a = cls.env['dl.contract.type'].create({
            'name': 'Test Fixed Contract A',
            'code': 'TEST_FIXED_A',
            'duration_type': 'fixed',
            'default_duration_months': 12,
            'company_id': cls.company_a.id,
        })

        cls.contract_type_indefinite_b = cls.env['dl.contract.type'].create({
            'name': 'Test Indefinite B',
            'code': 'TEST_INDEF_B',
            'duration_type': 'indefinite',
            'company_id': cls.company_b.id,
        })

        # Tạo Dummy DOCX file in base64 cho Wizard tests
        # Đây là 1 file zip/docx hợp lệ tối giản nhất (cực nhỏ)
        dummy_docx_base64 = b'UEsDBBQAAAAIADFfXVIAAABMAAAATAAAABAAAABkb2NQcm9wcy9hcHAueG1sPKzUyA+gH8hMw'
        
        cls.template_a = cls.env['dl.contract.template'].create({
            'name': 'Template A',
            'contract_type_id': cls.contract_type_fixed_a.id,
            'company_id': cls.company_a.id,
            'template_file': base64.b64encode(b"dummy data"), # Fake data just for testing if wizard fails appropriately
        })

    # --- BASIC TESTS (01 -> 07) ---
    def test_01_contract_creation_and_wage_compute(self):
        contract = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 10000000,
            'allowance': 2000000,
            'date_start': fields.Date.today(),
            'company_id': self.company_a.id,
        })
        self.assertEqual(contract.total_wage, 12000000)
        
        contract._onchange_contract_type_id()
        expected_date_end = contract.date_start + relativedelta(months=12, days=-1)
        self.assertEqual(contract.date_end, expected_date_end)

    def test_02_contract_confirmation_and_salary_history(self):
        contract = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 10000000,
            'date_start': fields.Date.today(),
            'company_id': self.company_a.id,
        })
        contract.action_confirm()
        self.assertEqual(contract.state, 'active')

        history = self.env['dl.salary.history'].search([('contract_id', '=', contract.id)])
        self.assertEqual(len(history), 1)
        self.assertEqual(history.old_wage, 0)
        self.assertEqual(history.new_wage, 10000000)

        contract.write({'wage': 15000000})
        history = self.env['dl.salary.history'].search([('contract_id', '=', contract.id)], order="id desc")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].difference, 5000000)

    def test_03_contract_expiry_and_employee_state(self):
        today = fields.Date.today()
        contract = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 5000000,
            'date_start': today - relativedelta(days=100),
            'date_end': today + relativedelta(days=10),
            'company_id': self.company_a.id,
        })
        contract.action_confirm()
        self.assertEqual(contract.x_days_to_expire, 10)
        self.assertTrue(contract.x_is_expiring_soon)

        self.employee_a.invalidate_recordset()
        self.assertEqual(self.employee_a.dl_contract_state, 'expiring_soon')

    def test_04_cron_job_expiration(self):
        today = fields.Date.today()
        contract = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 5000000,
            'date_start': today - relativedelta(days=100),
            'date_end': today - relativedelta(days=2),
            'state': 'active',
            'company_id': self.company_a.id,
        })
        self.env['dl.contract']._cron_check_expired()
        self.assertEqual(contract.state, 'expired')
        self.assertEqual(contract.x_days_to_expire, 0)

    def test_05_contract_renew(self):
        today = fields.Date.today()
        contract = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 5000000,
            'date_start': today - relativedelta(days=100),
            'date_end': today,
            'state': 'active',
            'company_id': self.company_a.id,
        })
        action = contract.action_renew()
        self.assertEqual(contract.state, 'renewed')
        new_contract = self.env['dl.contract'].browse(action.get('res_id'))
        self.assertEqual(new_contract.state, 'draft')

    def test_06_validation_constraints(self):
        contract = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 0,
            'date_start': fields.Date.today(),
            'company_id': self.company_a.id,
        })
        with self.assertRaises(ValidationError):
            contract.action_confirm()

    def test_07_sql_constraints_multi_company(self):
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env['dl.contract.type'].create({
                    'name': 'Duplicate Code',
                    'code': 'TEST_FIXED_A', 
                    'duration_type': 'indefinite',
                    'company_id': self.company_a.id,
                })

    # --- ADVANCED QUALITY TESTS (08 -> 17) ---

    def test_08_wizard_generation_empty_fields(self):
        """Test wizard với employee thiếu nhiều thông tin cá nhân"""
        # Đảm bảo employee_a không có thông tin sdt, địa chỉ...
        self.employee_a.write({
            'private_street': False,
            'private_phone': False,
            'identification_id': False,
        })
        contract = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 5000000,
            'date_start': fields.Date.today(),
            'company_id': self.company_a.id,
        })
        
        wizard = self.env['dl.contract.generate.wizard'].with_context(default_contract_id=contract.id, default_template_id=self.template_a.id).create({})
        
        # Test generation runs and handles Exception gracefully because python-docx throws "File is not a zip file" on our fake data.
        with self.assertRaisesRegex(UserError, "Lỗi khi đọc file mẫu"):
            wizard.action_generate()
            
    def test_09_wizard_generation_no_template_file(self):
        """Test wizard sẽ văng lỗi khi template bị rỗng (chưa upload)"""
        empty_template = self.env['dl.contract.template'].create({
            'name': 'Empty Template',
            'company_id': self.company_a.id,
        })
        contract = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 5000000,
            'date_start': fields.Date.today(),
            'company_id': self.company_a.id,
        })
        
        wizard = self.env['dl.contract.generate.wizard'].with_context(default_contract_id=contract.id, default_template_id=empty_template.id).create({})
        with self.assertRaisesRegex(UserError, "chưa có file mẫu"):
            wizard.action_generate()

    def test_10_multi_company_security_rules(self):
        """Test User B (Company B) không thể thấy Contract của Company A"""
        contract_a = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 5000000,
            'date_start': fields.Date.today(),
            'company_id': self.company_a.id,
        })
        
        # User B cố gắng truy cập Contract của Công ty A
        with self.assertRaises(AccessError):
            contract_a.with_user(self.user_b).read(['name'])

    def test_11_multi_company_domain_filtering(self):
        """Test User A tạo hợp đồng không thể gắn Loại hợp đồng của Company B"""
        with self.assertRaises(Exception): # ValidationError from check_company
            with self.env.cr.savepoint():
                contract = self.env['dl.contract'].with_user(self.user_a).create({
                    'employee_id': self.employee_a.id,
                    'contract_type_id': self.contract_type_indefinite_b.id, # Cố ý dùng type B
                    'wage': 5000000,
                    'date_start': fields.Date.today(),
                })
                contract._check_company()

    def test_12_cascading_deletion(self):
        """Test việc xóa Hợp đồng sẽ tự động cascade xóa Lịch sử Lương"""
        contract = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 5000000,
            'date_start': fields.Date.today(),
            'company_id': self.company_a.id,
        })
        contract.action_confirm()
        history_ids = self.env['dl.salary.history'].search([('contract_id', '=', contract.id)])
        self.assertTrue(history_ids)
        
        contract.unlink()
        
        # Lịch sử lương phải biến mất
        history_after = self.env['dl.salary.history'].search([('id', 'in', history_ids.ids)])
        self.assertFalse(history_after)

    def test_13_multiple_contracts_employee_state(self):
        """Kiểm tra employee.dl_current_contract_id khi có nhiều hợp đồng"""
        today = fields.Date.today()
        # HĐ 1 đã hết hạn
        c1 = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 10,
            'date_start': today - relativedelta(years=2),
            'date_end': today - relativedelta(years=1),
            'state': 'expired',
            'company_id': self.company_a.id,
        })
        
        # HĐ 2 đang active
        c2 = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 20,
            'date_start': today - relativedelta(months=5),
            'date_end': today + relativedelta(months=5),
            'state': 'active',
            'company_id': self.company_a.id,
        })
        
        # HĐ 3 đang draft
        c3 = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 30,
            'date_start': today + relativedelta(months=5),
            'date_end': today + relativedelta(months=17),
            'state': 'draft',
            'company_id': self.company_a.id,
        })

        self.employee_a.invalidate_recordset()
        # Hệ thống phải chọn c2 vì nó đang active
        self.assertEqual(self.employee_a.dl_current_contract_id.id, c2.id)

        # Chấm dứt c2
        c2.action_terminate()
        self.employee_a.invalidate_recordset()
        # Không có cái active nào, c3 là mới nhất (draft)
        self.assertEqual(self.employee_a.dl_current_contract_id.id, c3.id)

    def test_14_action_terminate(self):
        """Kiểm tra hành động Chấm dứt HĐ"""
        contract = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 5000000,
            'date_start': fields.Date.today(),
            'company_id': self.company_a.id,
        })
        contract.action_confirm()
        self.assertEqual(contract.state, 'active')
        
        contract.action_terminate()
        self.assertEqual(contract.state, 'terminated')
        
        self.employee_a.invalidate_recordset()
        self.assertEqual(self.employee_a.dl_contract_state, 'expired')

    def test_15_contract_write_wage_history(self):
        """Test: Khi thay đổi lương 2 lần, sinh ra 2 lịch sử đúng mức chênh lệch"""
        contract = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 100,
            'date_start': fields.Date.today(),
            'company_id': self.company_a.id,
        })
        contract.action_confirm() # Tạo history 1 (0 -> 100)
        
        contract.write({'wage': 150}) # Tạo history 2 (100 -> 150)
        contract.write({'wage': 120}) # Tạo history 3 (150 -> 120)
        
        histories = self.env['dl.salary.history'].search([('contract_id', '=', contract.id)], order='id asc')
        self.assertEqual(len(histories), 3)
        self.assertEqual(histories[0].difference, 100)
        self.assertEqual(histories[1].difference, 50)
        self.assertEqual(histories[2].difference, -30)

    def test_16_expiring_soon_thresholds(self):
        """Test chính xác ranh giới 30 ngày của expiring_soon"""
        today = fields.Date.today()
        c_31_days = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 10,
            'state': 'active',
            'date_end': today + relativedelta(days=31),
        })
        c_30_days = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 10,
            'state': 'active',
            'date_end': today + relativedelta(days=30),
        })
        c_29_days = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 10,
            'state': 'active',
            'date_end': today + relativedelta(days=29),
        })

        self.assertFalse(c_31_days.x_is_expiring_soon)
        self.assertTrue(c_30_days.x_is_expiring_soon)
        self.assertTrue(c_29_days.x_is_expiring_soon)

    def test_17_sequence_company_force(self):
        """Test: Mã HĐ sinh ra không bị null hoặc rỗng, và seq tuân thủ ir.sequence"""
        contract = self.env['dl.contract'].with_user(self.user_b).create({
            'employee_id': self.employee_b.id,
            'contract_type_id': self.contract_type_indefinite_b.id,
            'wage': 100,
            'date_start': fields.Date.today(),
            'company_id': self.company_b.id,
        })
        
        self.assertTrue(contract.name)
        self.assertNotEqual(contract.name, 'New')
        self.assertIn('DL-HD', contract.name)

    def test_18_default_wage_from_type(self):
        """Test: Khi thay đổi Loại hợp đồng, Lương tự động nhảy theo Lương mặc định"""
        self.contract_type_fixed_a.write({'default_wage': 6100000})
        
        contract = self.env['dl.contract'].new({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'date_start': fields.Date.today(),
            'company_id': self.company_a.id,
        })
        
        # Mô phỏng sự kiện onchange khi người dùng chọn loại hợp đồng trên giao diện
        contract._onchange_contract_type_id()
        self.assertEqual(contract.wage, 6100000)

    def test_19_dynamic_contract_sequence(self):
        """Test sinh số hợp đồng động theo mã loại hợp đồng"""
        # Tạo loại hợp đồng mới có code là 'CTH'
        type_cth = self.env['dl.contract.type'].create({
            'name': 'Hợp đồng có thời hạn CTH',
            'code': 'CTH',
            'duration_type': 'fixed',
            'company_id': self.company_a.id,
        })
        # Tạo hợp đồng
        contract = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': type_cth.id,
            'wage': 5000000,
            'date_start': fields.Date.today(),
            'company_id': self.company_a.id,
        })
        current_year = fields.Date.today().strftime('%Y')
        expected_prefix = f"DL-HD/CTH/{current_year}/"
        self.assertTrue(contract.name.startswith(expected_prefix))
        self.assertEqual(len(contract.name), len(expected_prefix) + 5) # padding = 5

    def test_20_wizard_default_template(self):
        """Test wizard tự động điền template mặc định từ loại hợp đồng"""
        # Gán template mặc định cho loại hợp đồng
        self.contract_type_fixed_a.write({
            'template_id': self.template_a.id
        })
        # Tạo hợp đồng
        contract = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 5000000,
            'date_start': fields.Date.today(),
            'company_id': self.company_a.id,
        })
        # Gọi wizard chỉ với default_contract_id
        wizard = self.env['dl.contract.generate.wizard'].with_context(default_contract_id=contract.id).create({})
        # Kiểm tra xem template_id có được điền đúng là template_a không
        self.assertEqual(wizard.template_id.id, self.template_a.id)

    def test_21_contract_rollback_state(self):
        """Test quay lại trạng thái trước đó của hợp đồng"""
        contract = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 5000000,
            'date_start': fields.Date.today(),
            'company_id': self.company_a.id,
        })
        self.assertEqual(contract.state, 'draft')
        self.assertFalse(contract.x_previous_state)

        # Chuyển sang active
        contract.action_confirm()
        self.assertEqual(contract.state, 'active')
        self.assertEqual(contract.x_previous_state, 'draft')

        # Chuyển sang expired
        contract.action_expire()
        self.assertEqual(contract.state, 'expired')
        self.assertEqual(contract.x_previous_state, 'active')

        # Quay lại trạng thái trước (từ expired về active)
        contract.action_set_to_previous_state()
        self.assertEqual(contract.state, 'active')
        self.assertFalse(contract.x_previous_state) # Đã reset sau khi rollback

    def test_22_active_contract_employee_info(self):
        """Test trường compute x_active_contract_department_id và x_active_contract_job_title trên employee"""
        # Tạo phòng ban test
        dept = self.env['hr.department'].create({
            'name': 'Phòng Sản Xuất Test',
            'company_id': self.company_a.id,
        })
        # Tạo hợp đồng dạng nháp
        contract = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': self.contract_type_fixed_a.id,
            'wage': 5000000,
            'date_start': fields.Date.today(),
            'company_id': self.company_a.id,
            'department_id': dept.id,
            'job_title': 'Công nhân tiện CNC',
        })
        self.employee_a.invalidate_recordset()
        # Trạng thái nháp nên 2 trường phải trống
        self.assertFalse(self.employee_a.x_active_contract_department_id)
        self.assertFalse(self.employee_a.x_active_contract_job_title)

        # Xác nhận hợp đồng để active
        contract.action_confirm()
        self.employee_a.invalidate_recordset()
        # Đã active nên phải nhận đúng thông tin của hợp đồng này
        self.assertEqual(self.employee_a.x_active_contract_department_id.id, dept.id)
        self.assertEqual(self.employee_a.x_active_contract_job_title, 'Công nhân tiện CNC')

        # Chuyển sang expired
        contract.action_expire()
        self.employee_a.invalidate_recordset()
        # Đã hết hiệu lực nên phải quay về trống
        self.assertFalse(self.employee_a.x_active_contract_department_id)
        self.assertFalse(self.employee_a.x_active_contract_job_title)

    def test_23_scan_doc_zip_download(self):
        """Test chức năng tải về zip nhiều tài liệu scan cùng lúc"""
        # 1. Tạo các tài liệu scan mẫu cho nhân viên (đặt x_is_digitized = True)
        doc1 = self.env['dl.employee.scan.doc'].create({
            'name': 'CCCD Nguyễn Văn A',
            'employee_id': self.employee_a.id,
            'file_data': base64.b64encode(b"Dummy PDF Content 1"),
            'file_name': 'cccd_a.pdf',
            'doc_type': 'id_card',
            'x_is_digitized': True,
        })
        doc2 = self.env['dl.employee.scan.doc'].create({
            'name': 'Hợp đồng lao động Nguyễn Văn A',
            'employee_id': self.employee_a.id,
            'file_data': base64.b64encode(b"Dummy PDF Content 2"),
            'file_name': 'hdld_a.pdf',
            'doc_type': 'contract',
            'x_is_digitized': True,
        })
        
        # 2. Test gọi wizard với active_ids của doc1 và doc2
        wizard = self.env['dl.scan.doc.zip.wizard'].with_context(
            active_ids=[doc1.id, doc2.id],
            active_model='dl.employee.scan.doc'
        ).create({})
        
        self.assertEqual(wizard.count, 2)
        self.assertTrue(wizard.file_data)
        self.assertTrue(wizard.file_name.startswith("Tai_lieu_scan_"))
        self.assertTrue(wizard.file_name.endswith(".zip"))
        
        # Thử giải nén kiểm tra nội dung
        zip_data = base64.b64decode(wizard.file_data)
        import io, zipfile
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
            filenames = zip_file.namelist()
            self.assertEqual(len(filenames), 2)
            
            # Tên file mong đợi theo format {employee_name}_{file_name}
            expected_name1 = f"{self.employee_a.name.replace(' ', '_')}_cccd_a.pdf"
            expected_name2 = f"{self.employee_a.name.replace(' ', '_')}_hdld_a.pdf"
            self.assertIn(expected_name1, filenames)
            self.assertIn(expected_name2, filenames)
            
            # Kiểm tra nội dung
            self.assertEqual(zip_file.read(expected_name1), b"Dummy PDF Content 1")
            self.assertEqual(zip_file.read(expected_name2), b"Dummy PDF Content 2")
            
        # 3. Test trường hợp gọi wizard không truyền active_ids
        with self.assertRaises(UserError):
            self.env['dl.scan.doc.zip.wizard'].with_context(active_ids=[]).create({})

    def test_24_scan_doc_digitized_filtering(self):
        """Test phân lọc tài liệu được số hoá và tài liệu tải lên thủ công"""
        self.employee_a.identification_id = '123456789012'
        
        # 1. Tạo tài liệu thủ công từ tab (mặc định x_is_digitized = False)
        doc_manual = self.env['dl.employee.scan.doc'].create({
            'name': 'Tài liệu thủ công',
            'employee_id': self.employee_a.id,
            'file_data': base64.b64encode(b"Dummy manual PDF"),
            'file_name': 'manual.pdf',
            'doc_type': 'other',
        })
        self.assertFalse(doc_manual.x_is_digitized)
        
        # 2. Tạo tài liệu qua wizard số hoá
        attach = self.env['ir.attachment'].create({
            'name': 'ocr_test.pdf',
            'datas': base64.b64encode(b"Dummy OCR PDF"),
            'res_model': 'dl.digitize.contract.wizard',
        })
        
        wizard = self.env['dl.digitize.contract.wizard'].create({
            'attachment_ids': [(6, 0, [attach.id])],
            'doc_type': 'contract',
            'doc_note': 'Test số hoá',
        })
        
        # Thiết lập dòng line
        wizard.line_ids = [(0, 0, {
            'attachment_id': attach.id,
            'extracted_cccd': '123456789012',
            'extracted_name': self.employee_a.name,
            'ocr_confidence': 'high',
            'matched_employee_id': self.employee_a.id,
            'action_type': 'link',
            'status': 'pending',
        })]
        wizard.state = 'review'
        
        # Thực hiện lưu
        wizard.action_confirm_save()
        
        # Tìm xem tài liệu đã tạo có x_is_digitized = True
        doc_digitized = self.env['dl.employee.scan.doc'].search([
            ('employee_id', '=', self.employee_a.id),
            ('x_is_digitized', '=', True)
        ])
        self.assertTrue(doc_digitized)
        self.assertEqual(len(doc_digitized), 1)
        self.assertEqual(doc_digitized.note, 'Test số hoá')
        
        # 3. Test câu lệnh SQL update dữ liệu cũ trong init()
        doc_old = self.env['dl.employee.scan.doc'].create({
            'name': 'HĐ scan - Nguyễn Văn A - 01/01/2026',
            'employee_id': self.employee_a.id,
            'file_data': base64.b64encode(b"Old PDF"),
            'file_name': 'old.pdf',
        })
        # Bắt buộc x_is_digitized thành False bằng SQL (để bỏ qua default value của create)
        self.env.cr.execute("UPDATE dl_employee_scan_doc SET x_is_digitized = FALSE WHERE id = %s", [doc_old.id])
        doc_old.invalidate_recordset()
        self.assertFalse(doc_old.x_is_digitized)
        
        # Chạy hàm init để update
        self.env['dl.employee.scan.doc'].init()
        doc_old.invalidate_recordset()
        self.assertTrue(doc_old.x_is_digitized)

    def test_25_company_prefix_sequence(self):
        """Test sinh số hợp đồng khi thay đổi mã cấu hình công ty x_wood_prefix"""
        # 1. Đổi prefix của công ty thành 'QTP'
        self.company_a.x_wood_prefix = 'QTP'
        
        # 2. Tạo loại hợp đồng mới có code là 'CTH'
        type_cth = self.env['dl.contract.type'].create({
            'name': 'Hợp đồng CTH QTP',
            'code': 'CTH',
            'duration_type': 'fixed',
            'company_id': self.company_a.id,
        })
        
        # 3. Tạo hợp đồng
        contract = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': type_cth.id,
            'wage': 5000000,
            'date_start': fields.Date.today(),
            'company_id': self.company_a.id,
        })
        
        current_year = fields.Date.today().strftime('%Y')
        expected_prefix = f"QTP-HD/CTH/{current_year}/"
        self.assertTrue(contract.name.startswith(expected_prefix))
        
        # 4. Thay đổi mã công ty một lần nữa thành 'VIP'
        self.company_a.x_wood_prefix = 'VIP'
        
        # Tạo hợp đồng tiếp theo, mã mới phải thay đổi prefix theo 'VIP'
        contract_vip = self.env['dl.contract'].create({
            'employee_id': self.employee_a.id,
            'contract_type_id': type_cth.id,
            'wage': 6000000,
            'date_start': fields.Date.today(),
            'company_id': self.company_a.id,
        })
        expected_prefix_vip = f"VIP-HD/CTH/{current_year}/"
        self.assertTrue(contract_vip.name.startswith(expected_prefix_vip))




