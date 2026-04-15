from odoo import models, fields, api, _
from odoo.exceptions import UserError
from markupsafe import Markup

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

        # Bước đặc thù: Xử lý Nhặt ván
        for emp_id, data in worker_data.items():
            if data['is_nhat_van'] and data['output_share'] > 0:
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
        group_pools = {} 
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
            base_salary = unit_price * data['hours']
            
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
        
        # Bước 6: Tập hợp cảnh báo
        warnings = {
            'over_hours': [],
            'missing_output': [],
            'missing_attendance': []
        }
        for emp_id, data in worker_data.items():
            emp_name = self.env['hr.employee'].browse(emp_id).name
            if data['hours'] > 1.0:
                warnings['over_hours'].append(emp_name)
            if data['hours'] > 0 and data['money'] == 0:
                warnings['missing_output'].append(emp_name)
            if data['money'] > 0 and data['hours'] == 0:
                warnings['missing_attendance'].append(emp_name)

        warning_summary = []
        if warnings['over_hours']:
            warning_summary.append("⚠️ TỔNG CÔNG > 1.0: " + ", ".join(warnings['over_hours']))
        if warnings['missing_output']:
            warning_summary.append("⚠️ CÓ CÔNG - THIẾU SẢN LƯỢNG: " + ", ".join(warnings['missing_output']))
        if warnings['missing_attendance']:
            warning_summary.append("❌ CÓ SẢN LƯỢNG - CHƯA CHẤM CÔNG: " + ", ".join(warnings['missing_attendance']))

        if result_vals:
            self.env['dl.daily.pooling.result'].create(result_vals)

        # Hiển thị thông báo kết quả qua Wizard Summary
        message = Markup(_("<div style='font-size:16px; margin-bottom:15px;'>✅ <b>Đã tính toán xong lương cho %d nhân viên.</b></div>")) % len(result_vals)
        if warning_summary:
            warn_html = Markup("").join(Markup("<div style='border-left: 4px solid #f0ad4e; background: #fcf8e3; padding: 10px; margin-bottom: 15px;'>%s</div>") % w for w in warning_summary)
            message += Markup("<b style='color:#a94442; font-size:15px; display:block; margin-bottom:10px;'>🚨 %s</b>%s") % (
                _("CẢNH BÁO DỮ LIỆU BẤT THƯỜNG:"),
                warn_html
            )
        
        summary_wizard = self.env['dl.pooling.summary.wizard'].create({
            'message': message,
            'date': self.date
        })

        return {
            'name': _('Tóm tắt kết quả tính toán'),
            'type': 'ir.actions.act_window',
            'res_model': 'dl.pooling.summary.wizard',
            'view_mode': 'form',
            'res_id': summary_wizard.id,
            'target': 'new',
        }

class PoolingSummaryWizard(models.TransientModel):
    _name = 'dl.pooling.summary.wizard'
    _description = 'Wizard hiển thị tóm tắt kết quả tính toán'

    message = fields.Html(string='Thông báo')
    date = fields.Date(string='Ngày')

    def action_view_results(self):
        """Action for the button in Summary Wizard"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Kết quả cào bằng lương'),
            'res_model': 'dl.daily.pooling.result',
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('date', '=', self.date)],
            'context': {'search_default_group_by_source_group': 1},
            'target': 'current',
        }
