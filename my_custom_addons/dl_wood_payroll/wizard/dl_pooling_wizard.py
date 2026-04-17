from odoo import models, fields, api, _
from odoo.exceptions import UserError
from markupsafe import Markup

class PoolingWizard(models.TransientModel):
    _name = 'dl.pooling.wizard'
    _description = 'Wizard tính toán cào bằng lương tổ'

    calc_type = fields.Selection([
        ('daily', 'Tính 1 ngày'),
        ('month_to_date', 'Từ đầu tháng đến ngày chọn')
    ], string='Kiểu tính toán', default='daily', required=True)
    
    date = fields.Date(string='Ngày (mốc)', default=fields.Date.today(), required=True)

    @api.model
    def cron_recalculate_previous_month(self):
        """Cronjob chạy vào mùng 1, 2 hàng tháng"""
        today = fields.Date.today()
        if today.day in [1, 2]:
            from datetime import timedelta
            first_day_of_current = today.replace(day=1)
            last_day_of_prev = first_day_of_current - timedelta(days=1)
            first_day_of_prev = last_day_of_prev.replace(day=1)
            
            self._execute_calculation_range(first_day_of_prev, last_day_of_prev)

    def _get_monthly_attendance(self, employee_id, date):
        """Tính tổng số công của nhân viên trong tháng chứa date"""
        start_date = date.replace(day=1)
        import calendar
        _, last_day = calendar.monthrange(date.year, date.month)
        end_date = date.replace(day=last_day)
        
        logs = self.env['dl.worker.log.line'].search([
            ('employee_id', '=', employee_id),
            ('production_log_id.date', '>=', start_date),
            ('production_log_id.date', '<=', end_date),
            ('production_log_id.state', 'in', ['confirmed', 'locked'])
        ])
        return sum(logs.mapped('worked_hours'))

    def _execute_calculation_range(self, start_date, end_date):
        """Thực thi tính toán cho một khoảng ngày"""
        from datetime import timedelta
        
        all_warnings = {
            'over_hours': set(),
            'missing_output': set(),
            'missing_attendance': set(),
            'missing_source_group': set(),
            'pending_handshakes': set()
        }
        total_created = 0
        
        current_date = start_date
        while current_date <= end_date:
            created_count, daily_warnings = self._calculate_for_day(current_date)
            total_created += created_count
            all_warnings['over_hours'].update(daily_warnings['over_hours'])
            all_warnings['missing_output'].update(daily_warnings['missing_output'])
            all_warnings['missing_attendance'].update(daily_warnings['missing_attendance'])
            if 'missing_source_group' in daily_warnings:
                all_warnings['missing_source_group'].update(daily_warnings['missing_source_group'])
            if 'pending_handshakes' in daily_warnings:
                all_warnings['pending_handshakes'].update(daily_warnings['pending_handshakes'])
            
            current_date += timedelta(days=1)
            
        warning_summary = []
        if all_warnings['pending_handshakes']:
            warning_summary.append(Markup("<b>🚫 LỖI CÒN NHÂN SỰ MƯỢN/CHO MƯỢN CHƯA DUYỆT BẮT TAY (KHÔNG TÍNH LƯƠNG ĐƯỢC):</b> %s") % (", ".join(list(all_warnings['pending_handshakes'])[:10]) + ("..." if len(all_warnings['pending_handshakes'])>10 else "")))
        if all_warnings['missing_source_group']:
            warning_summary.append(Markup("<b>🚫 LỖI THIẾU DỮ LIỆU TỔ GỐC (BỎ QUA KHÔNG TÍNH):</b> %s") % (", ".join(list(all_warnings['missing_source_group'])[:10]) + ("..." if len(all_warnings['missing_source_group'])>10 else "")))
        if all_warnings['over_hours']:
            warning_summary.append(Markup("<b>⚠️ TỔNG CÔNG > 1.0:</b> %s") % (", ".join(list(all_warnings['over_hours'])[:10]) + ("..." if len(all_warnings['over_hours'])>10 else "")))
        if all_warnings['missing_output']:
            warning_summary.append(Markup("<b>⚠️ CÓ CÔNG - THIẾU SẢN LƯỢNG:</b> %s") % (", ".join(list(all_warnings['missing_output'])[:10]) + ("..." if len(all_warnings['missing_output'])>10 else "")))
        if all_warnings['missing_attendance']:
            warning_summary.append(Markup("<b>❌ CÓ SẢN LƯỢNG - CHƯA CHẤM CÔNG:</b> %s") % (", ".join(list(all_warnings['missing_attendance'])[:10]) + ("..." if len(all_warnings['missing_attendance'])>10 else "")))
            
        return total_created, warning_summary

    def _calculate_for_day(self, calc_date):
        pricelist = self.env['dl.piece.rate.pricelist'].search([
            ('month', '=', calc_date.month),
            ('year', '=', calc_date.year),
            ('state', '=', 'confirmed')
        ], limit=1)
        
        daily_warnings = {'over_hours': [], 'missing_output': [], 'missing_attendance': [], 'missing_source_group': [], 'pending_handshakes': []}

        # Kiểm tra nếu còn yêu cầu chưa duyệt trong ngày
        pending_workers = self.env['dl.worker.log.line'].search([
            ('production_log_id.date', '=', calc_date),
            ('handshake_status', '=', 'pending')
        ])
        if pending_workers:
            daily_warnings['pending_handshakes'].extend(
                [f"{w.employee_id.name} ({calc_date.strftime('%d/%m')})" for w in pending_workers]
            )

        if not pricelist:
            # Ngầm bỏ qua nếu không có bảng giá. Khi cron chạy sẽ không bị lỗi crash.
            return 0, daily_warnings

        # Xóa kết quả cũ của ngày này
        self.env['dl.daily.pooling.result'].search([('date', '=', calc_date)]).unlink()

        logs = self.env['dl.production.log'].search([('date', '=', calc_date)])
        
        worker_data = {}
        attendance_lines = self.env['dl.daily.attendance.line'].search([('date', '=', calc_date)])
        for att in attendance_lines:
            emp_id = att.employee_id.id
            gid = att.employee_id.x_source_group_id.id
            if emp_id not in worker_data:
                worker_data[emp_id] = {
                    'hours': att.actual_work, 
                    'source_group_id': gid,
                    'earned_native_low': 0.0,
                    'earned_native_high': 0.0,
                    'earned_borrowed_low': 0.0,
                    'earned_borrowed_high': 0.0,
                }
            else:
                worker_data[emp_id]['hours'] += att.actual_work

        employee_ids = list(worker_data.keys())
        attendance_map = {}
        for emp_id in set(employee_ids):
            attendance_map[emp_id] = self._get_monthly_attendance(emp_id, calc_date)

        # Dictionary theo dõi tổng doanh thu và sản lượng theo Working Group (log.production_group_id)
        # Chỉ dùng cái này để update trường báo cáo "Doanh thu tổ" cho từng người
        group_daily_summary = {}

        for log in logs:
            dept = log.department_id
            if not dept: continue

            total_log_hours = sum(log.worker_line_ids.mapped('worked_hours'))
            if total_log_hours == 0: continue

            log_revenue_low = 0.0
            log_revenue_high = 0.0
            product_strings = []

            for prod_line in log.product_line_ids:
                price_line = pricelist.line_ids.filtered(
                    lambda l: l.department_id.id == dept.id and l.product_id.id == prod_line.product_id.id
                )
                if not price_line: continue
                price_line = price_line[0]
                
                log_revenue_low += prod_line.quantity * price_line.price_low
                log_revenue_high += prod_line.quantity * price_line.price_high
                
                # Format: Tên SP: Số lượng
                product_strings.append(f"{prod_line.product_id.name}: {prod_line.quantity}")

            # Lưu lại summary của tổ làm việc trong hôm nay
            wg_id = log.production_group_id.id
            if wg_id not in group_daily_summary:
                group_daily_summary[wg_id] = {'low': 0.0, 'high': 0.0, 'summary_list': []}
            group_daily_summary[wg_id]['low'] += log_revenue_low
            group_daily_summary[wg_id]['high'] += log_revenue_high
            group_daily_summary[wg_id]['summary_list'].extend(product_strings)

            for line in log.worker_line_ids:
                emp_id = line.employee_id.id
                share_factor = line.worked_hours / total_log_hours
                w_earned_low = log_revenue_low * share_factor
                w_earned_high = log_revenue_high * share_factor

                if emp_id not in worker_data:
                    gid = line.source_group_id.id or line.employee_id.x_source_group_id.id
                    worker_data[emp_id] = {
                        'hours': 0.0, 
                        'source_group_id': gid,
                        'earned_native_low': 0.0,
                        'earned_native_high': 0.0,
                        'earned_borrowed_low': 0.0,
                        'earned_borrowed_high': 0.0,
                    }
                
                if worker_data[emp_id]['source_group_id'] == log.production_group_id.id:
                    worker_data[emp_id]['earned_native_low'] += w_earned_low
                    worker_data[emp_id]['earned_native_high'] += w_earned_high
                else:
                    worker_data[emp_id]['earned_borrowed_low'] += w_earned_low
                    worker_data[emp_id]['earned_borrowed_high'] += w_earned_high

        # Gom Quỹ
        group_pools = {} 
        valid_worker_data = {}  # Filter out missing gid
        for emp_id, data in worker_data.items():
            gid = data['source_group_id']
            if not gid:
                emp_name = self.env['hr.employee'].browse(emp_id).name
                daily_warnings['missing_source_group'].append(f"{emp_name} ({calc_date.strftime('%d/%m')})")
                continue
                
            valid_worker_data[emp_id] = data
            if gid not in group_pools:
                group_pools[gid] = {'pool_low': 0.0, 'pool_high': 0.0, 'hours': 0.0}
            
            group_pools[gid]['pool_low'] += data['earned_native_low'] + data['earned_borrowed_low']
            group_pools[gid]['pool_high'] += data['earned_native_high'] + data['earned_borrowed_high']
            group_pools[gid]['hours'] += data['hours']

        result_vals = []
        for emp_id, data in valid_worker_data.items():
            gid = data['source_group_id']
            pool = group_pools[gid]
            
            unit_price_low = pool['pool_low'] / pool['hours'] if pool['hours'] > 0 else 0.0
            unit_price_high = pool['pool_high'] / pool['hours'] if pool['hours'] > 0 else 0.0
            
            is_high_diligence = attendance_map.get(emp_id, 0.0) >= pricelist.x_required_days
            final_unit_price = unit_price_high if is_high_diligence else unit_price_low
            
            base_salary = final_unit_price * data['hours']
            
            fines = self.env['dl.employee.fine'].search([
                ('employee_id', '=', emp_id),
                ('date', '=', calc_date)
            ])
            total_fine = sum(fines.mapped('amount'))
            final_salary = base_salary - total_fine
            
            display_total_contribution = data['earned_native_high'] + data['earned_borrowed_high']
            
            # Lấy Production Summary của tổ nguồn
            wg_summary = group_daily_summary.get(gid, {'low': 0.0, 'high': 0.0, 'summary_list': []})
            wg_summary_str = ", ".join(wg_summary['summary_list']) if wg_summary['summary_list'] else ""
            
            result_vals.append({
                'date': calc_date,
                'employee_id': emp_id,
                'source_group_id': gid,
                'actual_work_days': data['hours'],
                'contribution_amount': display_total_contribution,
                'native_contribution': data['earned_native_high'],
                'borrowed_contribution': data['earned_borrowed_high'],
                'is_loaned_worker': data['earned_borrowed_high'] > 0,
                'pool_unit_price': final_unit_price,
                'final_salary': final_salary,
                'group_revenue_low': wg_summary['low'],
                'group_revenue_high': wg_summary['high'],
                'group_production_summary': wg_summary_str
            })
        
        for emp_id, data in valid_worker_data.items():
            emp_name = self.env['hr.employee'].browse(emp_id).name
            fmt_name = f"{emp_name} ({calc_date.strftime('%d/%m')})"
            if data['hours'] > 1.0:
                daily_warnings['over_hours'].append(fmt_name)
            if data['hours'] > 0 and (data['earned_native_high'] + data['earned_borrowed_high']) == 0:
                daily_warnings['missing_output'].append(fmt_name)
            if (data['earned_native_high'] + data['earned_borrowed_high']) > 0 and data['hours'] == 0:
                daily_warnings['missing_attendance'].append(fmt_name)

        if result_vals:
            self.env['dl.daily.pooling.result'].create(result_vals)

        return len(result_vals), daily_warnings

    def action_calculate(self):
        self.ensure_one()
        
        if self.calc_type == 'daily':
            start_date = self.date
            end_date = self.date
        else:
            start_date = self.date.replace(day=1)
            end_date = self.date

        total_records, warning_summary = self._execute_calculation_range(start_date, end_date)
        
        if total_records == 0:
            raise UserError(_("Không có dữ liệu hợp lệ (hoặc thiếu Bảng giá xác nhận) để tính toán trong khoảng thời gian này."))

        message = Markup(_("<div style='font-size:16px; margin-bottom:15px;'>✅ <b>Đã tính toán xong lương cho tổng cộng %d bản ghi (ngày x nhân sự).</b></div>")) % total_records
        if warning_summary:
            warn_html = Markup("").join(Markup("<div style='border-left: 4px solid #f0ad4e; background: #fcf8e3; padding: 10px; margin-bottom: 15px;'>%s</div>") % w for w in warning_summary)
            message += Markup("<b style='color:#a94442; font-size:15px; display:block; margin-bottom:10px;'>🚨 %s</b>%s") % (
                _("TỔNG HỢP CẢNH BÁO:"),
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
