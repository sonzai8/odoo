# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools

class PayrollMatrixReport(models.Model):
    _inherit = 'dl.payroll.matrix.report'

    type = fields.Selection(selection_add=[
        ('sorting', 'Nhặt ván')
    ], ondelete={'sorting': 'cascade'})

    def init(self):
        # We need to call super() or rebuild the whole view if we want to add a UNION.
        # In Odoo SQL views, usually we have to rebuild the whole SELECT if it's a UNION.
        # But we can get the base query by looking at the parent's init or just re-defining it here.
        # Since the parent's init drops the view and creates it, we will do the same but with one more UNION.
        
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
                    COALESCE(emp.x_source_group_id, (SELECT id FROM dl_production_group LIMIT 1)) AS source_group_id,
                    log.service_name AS product_name,
                    1.0 AS quantity,
                    line.amount AS unit_price,
                    line.amount AS total_money,
                    line.currency_id AS currency_id,
                    'stevedore' AS type
                FROM dl_stevedore_log_line line
                JOIN dl_stevedore_log log ON line.stevedore_log_id = log.id
                JOIN hr_employee emp ON line.employee_id = emp.id
                WHERE log.state = 'confirmed'

                UNION ALL

                -- 3. Dữ liệu Lương Phơi ván (Veneer Drying)
                SELECT
                    log.id + 20000000 AS id,
                    log.date AS date,
                    log.employee_id AS employee_id,
                    COALESCE(emp.x_source_group_id, (SELECT id FROM dl_production_group LIMIT 1)) AS source_group_id,
                    'Nghiệm thu Phơi ván: ' || log.veneer_type || ' ' || log.thickness || 'ly ' || log.quality AS product_name,
                    log.quantity AS quantity,
                    log.unit_price AS unit_price,
                    log.total_amount AS total_money,
                    log.currency_id AS currency_id,
                    'drying' AS type
                FROM dl_veneer_drying_log log
                JOIN hr_employee emp ON log.employee_id = emp.id
                WHERE log.state = 'confirmed'

                UNION ALL

                -- 4. Dữ liệu Lương Nhặt ván (Wood Sorting)
                SELECT
                    line.id + 30000000 AS id,
                    log.date AS date,
                    line.employee_id AS employee_id,
                    COALESCE(emp.x_source_group_id, (SELECT id FROM dl_production_group LIMIT 1)) AS source_group_id,
                    'Nhặt ván: ' || COALESCE(line.qty_17, 0) + COALESCE(line.qty_20, 0) || ' bó' AS product_name,
                    COALESCE(line.qty_17, 0) + COALESCE(line.qty_20, 0) AS quantity,
                    CASE WHEN (COALESCE(line.qty_17, 0) + COALESCE(line.qty_20, 0)) > 0 
                         THEN line.amount / (COALESCE(line.qty_17, 0) + COALESCE(line.qty_20, 0)) 
                         ELSE 0 END AS unit_price,
                    line.amount AS total_money,
                    line.currency_id AS currency_id,
                    'sorting' AS type
                FROM dl_sorting_log_line line
                JOIN dl_sorting_log log ON line.log_id = log.id
                JOIN hr_employee emp ON line.employee_id = emp.id
                WHERE log.state = 'confirmed'
            )
        """ % self._table)
