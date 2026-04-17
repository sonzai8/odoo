# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools

class PayrollMatrixReport(models.Model):
    _name = 'dl.payroll.matrix.report'
    _description = 'Báo cáo Ma trận Lương Tổng hợp'
    _auto = False
    _order = 'date desc'

    date = fields.Date(string='Ngày', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', readonly=True)
    source_group_id = fields.Many2one('dl.production.group', string='Tổ (Bộ phận)', readonly=True)
    product_name = fields.Char(string='Nội dung công việc / Mặt hàng', readonly=True)
    quantity = fields.Float(string='Sản lượng / Số công', readonly=True)
    unit_price = fields.Monetary(string='Đơn giá', readonly=True, currency_field='currency_id')
    total_money = fields.Monetary(string='Thành tiền (Lương)', readonly=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', readonly=True)
    type = fields.Selection([
        ('pooling', 'Quy đổi/Cào bằng'),
        ('stevedore', 'Khoán trực tiếp'),
        ('drying', 'Phơi ván')
    ], string='Cơ chế lương', readonly=True)

    def init(self):
        # Kiểm tra xem các bảng phụ thuộc đã tồn tại trong DB chưa
        self.env.cr.execute("""
            SELECT count(*) 
            FROM information_schema.tables 
            WHERE table_name IN ('dl_daily_pooling_result', 'dl_stevedore_log_line', 'dl_veneer_drying_log')
        """)
        if self.env.cr.fetchone()[0] < 3:
            # Nếu chưa đủ các bảng thì chưa tạo View để tránh lỗi UndefinedTable
            return

        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                -- 1. Dữ liệu Lương cào bằng tổ (Pooling)
                SELECT
                    res.id AS id,
                    res.date AS date,
                    res.employee_id AS employee_id,
                    res.source_group_id AS source_group_id,
                    res.group_production_summary AS product_name,
                    res.actual_work_days AS quantity,
                    res.pool_unit_price AS unit_price,
                    res.final_salary AS total_money,
                    res.currency_id AS currency_id,
                    'pooling' AS type
                FROM dl_daily_pooling_result res
                
                UNION ALL
                
                -- 2. Dữ liệu Lương khoán Bốc vác (Stevedore)
                SELECT
                    line.id + 10000000 AS id,
                    line.date AS date,
                    line.employee_id AS employee_id,
                    line.x_source_group_id AS source_group_id,
                    task.name AS product_name,
                    line.quantity AS quantity,
                    CASE WHEN line.quantity > 0 THEN line.amount / line.quantity ELSE 0 END AS unit_price,
                    line.amount AS total_money,
                    line.currency_id AS currency_id,
                    'stevedore' AS type
                FROM dl_stevedore_log_line line
                JOIN dl_stevedore_log log ON line.log_id = log.id
                JOIN dl_stevedore_task task ON log.task_id = task.id
                WHERE log.state = 'confirmed'

                UNION ALL

                -- 3. Dữ liệu Lương Phơi ván (Veneer Drying)
                SELECT
                    line.id + 20000000 AS id,
                    line.date AS date,
                    line.employee_id AS employee_id,
                    line.x_source_group_id AS source_group_id,
                    'Phơi ván: ' || line.veneer_type || ' ' || line.thickness || 'ly ' || line.quality AS product_name,
                    line.quantity AS quantity,
                    line.unit_price AS unit_price,
                    line.total_amount AS total_money,
                    line.currency_id AS currency_id,
                    'drying' AS type
                FROM dl_veneer_drying_line line
                JOIN dl_veneer_drying_log log ON line.log_id = log.id
                WHERE log.state = 'confirmed'
            )
        """ % self._table)
