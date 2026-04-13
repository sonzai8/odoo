# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PoolingWizard(models.TransientModel):
    _name = 'dl.pooling.wizard'
    _description = 'Wizard tính toán cào bằng lương tổ'

    date = fields.Date(string='Ngày tính toán', default=fields.Date.today(), required=True)

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
        # { employee_id: { money_contribution: 0.0, work_days: 0.0, source_group_id: ID } }
        worker_data = {}

        # Bước 1 & 2: Tính doanh thu từng log và phân bổ cho nhân viên
        for log in logs:
            # Tìm đơn giá
            price_line = pricelist.line_ids.filtered(lambda l: l.workcenter_id == log.work_center_id)
            if not price_line:
                continue # Hoặc báo lỗi nếu cần
            
            price_line = price_line[0]
            base_price = price_line.price
            
            # Tính tổng công trong log
            total_log_hours = sum(log.worker_line_ids.mapped('worked_hours'))
            if total_log_hours == 0:
                continue

            for line in log.worker_line_ids:
                emp_id = line.employee_id.id
                if emp_id not in worker_data:
                    worker_data[emp_id] = {
                        'money': 0.0, 
                        'hours': 0.0, 
                        'source_group_id': line.source_group_id.id,
                        'is_nhat_van': log.work_center_id.x_is_nhat_van,
                        'output_share': 0.0 # Dùng cho Nhặt ván
                    }
                
                # Phân bổ sản lượng và giờ công
                share_factor = line.worked_hours / total_log_hours
                log_revenue = log.quantity * base_price
                
                # Nếu không phải Nhặt ván, tính tiền bình thường
                if not log.work_center_id.x_is_nhat_van:
                    worker_data[emp_id]['money'] += log_revenue * share_factor
                else:
                    # Nhặt ván: Tích lũy sản lượng để tính lũy tiến sau
                    worker_data[emp_id]['output_share'] += log.quantity * share_factor
                
                worker_data[emp_id]['hours'] += line.worked_hours

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
            final_salary = unit_price * data['hours']
            
            result_vals.append({
                'date': self.date,
                'employee_id': emp_id,
                'source_group_id': gid,
                'actual_work_days': data['hours'],
                'contribution_amount': data['money'],
                'pool_unit_price': unit_price,
                'final_salary': final_salary,
            })
        
        if result_vals:
            self.env['dl.daily.pooling.result'].create(result_vals)
            
        return {
            'type': 'ir.actions.act_window',
            'name': _('Kết quả cào bằng lương'),
            'res_model': 'dl.daily.pooling.result',
            'view_mode': 'list,form',
            'domain': [('date', '=', self.date)],
            'target': 'current',
        }
