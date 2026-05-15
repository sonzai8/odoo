# -*- coding: utf-8 -*-
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    dl_pit_personal_deduction = fields.Monetary(
        related='company_id.dl_pit_personal_deduction',
        string='Giảm trừ bản thân',
        readonly=False
    )
    dl_pit_dependent_deduction = fields.Monetary(
        related='company_id.dl_pit_dependent_deduction',
        string='Giảm trừ người phụ thuộc',
        readonly=False
    )
    def action_standardize_tax_departments(self):
        """Chuẩn hóa lại phòng ban thuế cho toàn bộ nhân viên của công ty hiện tại."""
        company = self.env.company
        employees = self.env['hr.employee'].sudo().search([
            ('company_id', '=', company.id),
            ('dl_tax_department_id', '!=', False)
        ])
        count = 0
        for emp in employees:
            current_dept = emp.dl_tax_department_id
            if current_dept.company_id != company:
                # Tìm phòng ban cùng tên ở đúng công ty hiện tại
                correct_dept = self.env['dl.tax.department'].sudo().search([
                    ('name', '=', current_dept.name),
                    ('company_id', '=', company.id)
                ], limit=1)
                
                if correct_dept:
                    emp.sudo().write({'dl_tax_department_id': correct_dept.id})
                    count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Hoàn tất chuẩn hóa',
                'message': f'Đã cập nhật đúng phòng ban cho {count} nhân viên.',
                'sticky': False,
                'type': 'success',
            }
        }

    def action_init_tax_departments(self):
        """Khởi tạo thủ công danh sách phòng ban thuế chuẩn cho công ty hiện tại."""
        self.env['dl.tax.department'].sudo()._seed_default_data(company_id=self.env.company.id)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Khởi tạo hoàn tất',
                'message': 'Đã cập nhật danh sách phòng ban thuế chuẩn cho công ty.',
                'type': 'success',
            }
        }

    def action_init_attendance_types(self):
        """Khởi tạo thủ công danh sách mã công chuẩn cho công ty hiện tại."""
        company = self.env.company
        att_types = [
            {'code': 'N', 'name': 'Công ngày (8h)', 'weight': 1.0, 'apply_to': 'normal', 'sequence': 10},
            {'code': 'N/2', 'name': 'Công ngày (4h)', 'weight': 0.5, 'apply_to': 'normal', 'sequence': 11},
            {'code': 'Đ', 'name': 'Công đêm (8h)', 'weight': 1.0, 'apply_to': 'normal', 'sequence': 20},
            {'code': 'Đ/2', 'name': 'Công đêm (4h)', 'weight': 0.5, 'apply_to': 'normal', 'sequence': 21},
            {'code': 'P', 'name': 'Nghỉ phép hưởng lương', 'weight': 1.0, 'apply_to': 'normal', 'sequence': 30},
            {'code': 'PL', 'name': 'Nghỉ lễ/Tết hưởng lương', 'weight': 1.0, 'apply_to': 'normal', 'sequence': 40},
            {'code': 'CP', 'name': 'Nghỉ có phép (Không lương)', 'weight': 0.0, 'apply_to': 'normal', 'sequence': 50},
            {'code': 'KP', 'name': 'Nghỉ không phép (Trừ KPI)', 'weight': 0.0, 'apply_to': 'normal', 'sequence': 60},
            {'code': 'Ô', 'name': 'Nghỉ ốm (BHXH)', 'weight': 0.0, 'apply_to': 'normal', 'sequence': 70},
            {'code': 'CÔ', 'name': 'Con ốm (BHXH)', 'weight': 0.0, 'apply_to': 'normal', 'sequence': 80},
            {'code': 'TS', 'name': 'Nghỉ thai sản', 'weight': 0.0, 'apply_to': 'normal', 'sequence': 90},
            {'code': 'DS', 'name': 'Nghỉ dưỡng sức', 'weight': 0.0, 'apply_to': 'normal', 'sequence': 100},
            {'code': 'ĐC', 'name': 'Ngày đổi ca', 'weight': 0.0, 'apply_to': 'normal', 'sequence': 110},
            {'code': 'CN', 'name': 'Cho nghỉ (Không lương)', 'weight': 0.0, 'apply_to': 'normal', 'sequence': 120},
            {'code': 'DL', 'name': 'Nghỉ du lịch', 'weight': 0.0, 'apply_to': 'normal', 'sequence': 130},
            {'code': 'NV', 'name': 'Ngày nghỉ việc', 'weight': 0.0, 'apply_to': 'normal', 'sequence': 140},
            {'code': 'KL', 'name': 'Nghỉ không lương', 'weight': 0.0, 'apply_to': 'normal', 'sequence': 150},
            {'code': '0.5N', 'name': 'Tăng ca ngày (0.5h)', 'weight': 0.0625, 'apply_to': 'overtime', 'ot_type': 'day', 'sequence': 200},
            {'code': '0.5Đ', 'name': 'Tăng ca đêm (0.5h)', 'weight': 0.0625, 'apply_to': 'overtime', 'ot_type': 'night', 'sequence': 201},
            {'code': 'CNN', 'name': 'Tăng ca Chủ Nhật ngày (8h)', 'weight': 1.0, 'apply_to': 'overtime', 'ot_type': 'day', 'sequence': 210},
            {'code': 'CNN/2', 'name': 'Tăng ca Chủ Nhật ngày (4h)', 'weight': 0.5, 'apply_to': 'overtime', 'ot_type': 'day', 'sequence': 211},
            {'code': 'CNĐ', 'name': 'Tăng ca Chủ Nhật đêm (8h)', 'weight': 1.0, 'apply_to': 'overtime', 'ot_type': 'night', 'sequence': 220},
            {'code': 'CNĐ/2', 'name': 'Tăng ca Chủ Nhật đêm (4h)', 'weight': 0.5, 'apply_to': 'overtime', 'ot_type': 'night', 'sequence': 221},
            {'code': 'LN', 'name': 'Tăng ca Lễ ngày (8h)', 'weight': 1.0, 'apply_to': 'overtime', 'ot_type': 'day', 'sequence': 230},
            {'code': 'LĐ', 'name': 'Tăng ca Lễ đêm (8h)', 'weight': 1.0, 'apply_to': 'overtime', 'ot_type': 'night', 'sequence': 231},
            {'code': '1LN', 'name': 'Làm thêm Lễ ngày (8h) - Cũ', 'weight': 1.0, 'apply_to': 'overtime', 'ot_type': 'day', 'sequence': 240},
            {'code': '0.5LN', 'name': 'Làm thêm Lễ ngày (4h) - Cũ', 'weight': 0.5, 'apply_to': 'overtime', 'ot_type': 'day', 'sequence': 241},
        ]
        
        count_created = 0
        count_updated = 0
        for vals in att_types:
            existing = self.env['dl.salary.kpi.attendance.type'].sudo().search([
                ('code', '=', vals['code']),
                ('company_id', '=', company.id)
            ])
            if existing:
                # Cập nhật thông tin nếu đã tồn tại (để sửa trọng số nếu cần)
                existing[0].write({
                    'name': vals['name'],
                    'weight': vals['weight'],
                    'apply_to': vals['apply_to'],
                    'ot_type': vals.get('ot_type'),
                    'sequence': vals['sequence']
                })
                count_updated += 1
            else:
                vals['company_id'] = company.id
                self.env['dl.salary.kpi.attendance.type'].sudo().create(vals)
                count_created += 1
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Khởi tạo hoàn tất',
                'message': f'Đã tạo mới {count_created} và cập nhật {count_updated} mã chấm công cho công ty.',
                'type': 'success',
            }
        }
