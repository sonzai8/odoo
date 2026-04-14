# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PoolingWizard(models.TransientModel):
    _name = 'dl.pooling.wizard'
    _description = 'Wizard tính toán cào bằng lương tổ'

    date = fields.Date(string='Ngày tính toán', default=fields.Date.today(), required=True)

    def _get_monthly_attendance(self, employee_id, date):
        """Tính tổng số công của nhân viên trong tháng"""
        start_date = date.replace(day=1)
        # Tìm ngày cuối tháng
        import calendar
        _, last_day = calendar.monthrange(date.year, date.month)
        end_date = date.replace(day=last_day)
        
        # Truy vấn tất cả các log line trong tháng
        logs = self.env['dl.worker.log.line'].search([
            ('employee_id', '=', employee_id),
            ('production_log_id.date', '>=', start_date),
            ('production_log_id.date', '<=', end_date),
            ('production_log_id.state', 'in', ['confirmed', 'locked'])
        ])
        return sum(logs.mapped('worked_hours'))

    def action_calculate(self):
        self.ensure_one()
        
        # 1. Lấy bảng giá đã xác nhận cho tháng của ngày này
        pricelist = self.env['dl.piece.rate.pricelist'].search([
            ('month', '=', self.date.month),
            ('year', '=', self.date.year),
            ('state', '=', 'confirmed')
        ], limit=1)
        
        if not pricelist:
            raise UserError(_("Không tìm thấy bảng giá xác nhận cho tháng %s/%s") % (self.date.month, self.date.year))

        # Xóa kết quả cũ nếu có
        self.env['dl.daily.pooling.result'].search([('date', '=', self.date)]).unlink()

        # 2. Lấy tất cả các bản ghi sản lượng trong ngày
        logs = self.env['dl.production.log'].search([('date', '=', self.date)])
        
        # Dictionary lưu trữ thông tin theo nhân viên: 
        worker_data = {}
        
        # 1.1 Khởi tạo dữ liệu từ Chấm công (Đảm bảo có mặt là có trong bảng lương)
        attendance_lines = self.env['dl.daily.attendance.line'].search([('date', '=', self.date)])
        for att in attendance_lines:
            emp_id = att.employee_id.id
            if emp_id not in worker_data:
                worker_data[emp_id] = {
                    'money': 0.0, 
                    'native_money': 0.0,
                    'borrowed_money': 0.0,
                    'hours': att.actual_work, 
                    'source_group_id': att.production_group_id.id,
                    'is_nhat_van': False,
                    'output_share': 0.0
                }
            else:
                # Nếu một người làm 2 nơi (trường hợp bất thường hoặc bổ trợ)
                worker_data[emp_id]['hours'] += att.actual_work

        # 1.5 Tính toán chuyên cần tháng cho tất cả nhân viên đã khởi tạo
        employee_ids = list(worker_data.keys())
        attendance_map = {}
        for emp_id in set(employee_ids):
            attendance_map[emp_id] = self._get_monthly_attendance(emp_id, self.date)

        # Bước 1 & 2: Tính doanh thu từng log và phân bổ cho nhân viên
        for log in logs:
            dept = log.department_id
            if not dept:
                continue

            # Bước 1 & 2: Tính doanh thu từng log và phân bổ cho nhân viên
            # Tính tổng công trong log
            total_log_hours = sum(log.worker_line_ids.mapped('worked_hours'))
            if total_log_hours == 0:
                continue

            for line in log.worker_line_ids:
                emp_id = line.employee_id.id
                
                # Tìm đơn giá cho sản phẩm/công đoạn
                # (Lưu ý: log có thể có nhiều sản phẩm, ta lặp qua từng sản phẩm trong log)
                log_revenue_person = 0.0
                
                # Kiểm tra chuyên cần của nhân viên này
                is_high_diligent = attendance_map.get(emp_id, 0.0) >= pricelist.x_required_days
                
                for prod_line in log.product_line_ids:
                    # Lấy đơn giá từ pricelist
                    price_line = pricelist.line_ids.filtered(
                        lambda l: l.department_id.id == dept.id and l.product_id.id == prod_line.product_id.id
                    )
                    if not price_line:
                        continue
                    
                    price_line = price_line[0]
                    # CHỌN GIÁ CAO HOẶC THẤP
                    unit_price = price_line.price_high if is_high_diligent else price_line.price_low
                    
                    # Phân bổ sản lượng và giờ công cho sản phẩm này
                    share_factor = line.worked_hours / total_log_hours
                    prod_revenue = prod_line.quantity * unit_price
                    log_revenue_person += prod_revenue * share_factor

                if emp_id not in worker_data:
                    # Trường hợp: Có sản lượng nhưng QUÊN chấm công (Sẽ bị cảnh báo đỏ)
                    worker_data[emp_id] = {
                        'money': 0.0, 
                        'native_money': 0.0,
                        'borrowed_money': 0.0,
                        'hours': 0.0, 
                        'source_group_id': line.source_group_id.id,
                        'is_nhat_van': False,
                        'output_share': 0.0
                    }
                
                # Cộng tiền sản lượng vào dữ liệu nhân viên
                if worker_data[emp_id]['source_group_id'] == log.production_group_id.id:
                    worker_data[emp_id]['native_money'] += log_revenue_person
                else:
                    worker_data[emp_id]['borrowed_money'] += log_revenue_person

                worker_data[emp_id]['money'] += log_revenue_person
                # Lưu ý: Không cộng data['hours'] ở đây vì 'hours' lấy từ Chấm công là chuẩn nhất
                # Nhưng nếu họ không có chấm công (hours=0), ta vẫn ghi nhận sản lượng cho họ

        # Bước đặc thù: Xử lý Nhặt ván cho các nhân viên đã tích lũy sản lượng
        for emp_id, data in worker_data.items():
            if data['is_nhat_van'] and data['output_share'] > 0:
                # Tìm lại đơn giá lũy tiến cho tổ Nhặt ván của nhân viên này 
                # (Giả định nhân viên làm ở tổ Nhặt ván nào đó trong ngày)
                # Để đơn giản, lấy Price Line từ pricelist tương ứng
                # (Trong thực tế có thể cần tìm chính xác tổ họ đã làm)
                # Ở đây ta sử dụng thông tin từ vòng lặp trước hoặc tìm lại
                
                # Tìm bất kỳ line nào của tổ Nhặt ván trong pricelist
                nhat_van_line = pricelist.line_ids.filtered(lambda l: l.workcenter_id.x_is_nhat_van)
                if nhat_van_line:
                    nvl = nhat_van_line[0]
                    threshold = nvl.x_threshold or 280
                    p_base = nvl.price
                    p_prog = nvl.x_progressive_price or p_base
                    
                    output = data['output_share']
                    if output <= threshold:
                        data['money'] = output * p_base
                    else:
                        data['money'] = (threshold * p_base) + ((output - threshold) * p_prog)

        # Bước 3 & 4: Gom quỹ lương theo Tổ Gốc (Source Group)
        group_pools = {} # { group_id: { total_money: 0.0, total_hours: 0.0 } }
        for emp_id, data in worker_data.items():
            gid = data['source_group_id']
            if gid not in group_pools:
                group_pools[gid] = {'money': 0.0, 'hours': 0.0}
            
            group_pools[gid]['money'] += data['money']
            group_pools[gid]['hours'] += data['hours']

        # Bước 5: Tính đơn giá 1 công và tạo kết quả
        result_vals = []
        for emp_id, data in worker_data.items():
            gid = data['source_group_id']
            pool = group_pools[gid]
            
            unit_price = pool['money'] / pool['hours'] if pool['hours'] > 0 else 0
            
            # Calculate Base Salary
            base_salary = unit_price * data['hours']
            
            # Subtract Fines for this day
            fines = self.env['dl.employee.fine'].search([
                ('employee_id', '=', emp_id),
                ('date', '=', self.date)
            ])
            total_fine = sum(fines.mapped('amount'))
            final_salary = base_salary - total_fine
            
            result_vals.append({
                'date': self.date,
                'employee_id': emp_id,
                'source_group_id': gid,
                'actual_work_days': data['hours'],
                'contribution_amount': data['money'],
                'native_contribution': data['native_money'],
                'borrowed_contribution': data['borrowed_money'],
                'is_loaned_worker': data['borrowed_money'] > 0,
                'pool_unit_price': unit_price,
                'final_salary': final_salary,
            })
        
        # Bước 6: Tập hợp cảnh báo và thực hiện tính toán
        warning_summary = []
        for emp_id, data in worker_data.items():
            emp_name = self.env['hr.employee'].browse(emp_id).name
            # Cảnh báo 1: Tổng công vượt quá 1.0
            if data['hours'] > 1.0:
                warning_summary.append(_("Nhân viên %s: Tổng công trong ngày là %.2f ( > 1.0)") % (emp_name, data['hours']))
            
            # Cảnh báo thì đã xử lý ở bước tạo dữ liệu, ở đây ta chỉ cần thực hiện ghi log hoặc hiển thị
            # Cảnh báo 2: Có chấm công nhưng tiền contribution = 0
            if data['hours'] > 0 and data['money'] == 0:
                warning_summary.append(_("Nhân viên %s: Có chấm công đi làm nhưng chưa có sản lượng/không tham gia tổ nào.") % emp_name)

            # Cảnh báo 3: Có sản lượng nhưng không có chấm công
            if data['money'] > 0 and data['hours'] == 0:
                warning_summary.append(_("Nhân viên %s: Đã có sản lượng ghi nhận nhưng CHƯA ĐƯỢC CHẤM CÔNG.") % emp_name)

        if result_vals:
            self.env['dl.daily.pooling.result'].create(result_vals)

        # Hiển thị thông báo kết quả
        message = _("Đã tính toán xong lương cho %d nhân viên.") % len(result_vals)
        if warning_summary:
            message += "\n\n" + _("CẢNH BÁO DỮ LIÊU BẤT THƯỜNG:") + "\n- " + "\n- ".join(warning_summary[:15])
            if len(warning_summary) > 15:
                message += "\n..."
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Kết quả tính toán'),
                'message': message,
                'sticky': True,
                'type': 'warning' if warning_summary else 'success',
                'next': {
                    'type': 'ir.actions.act_window',
                    'name': _('Kết quả cào bằng lương'),
                    'res_model': 'dl.daily.pooling.result',
                    'view_mode': 'list,form',
                    'views': [[False, 'list'], [False, 'form']],
                    'domain': [('date', '=', self.date)],
                    'target': 'current',
                }
            }
        }
