import os
import sys

# Mock odoo environment
def check():
    import odoo
    from odoo import api, registry
    
    config_file = '/Users/sonzai/dev/odoo 19/odoo/odoo.conf'
    odoo.tools.config.parse_config(['-c', config_file])
    db_name = 'odoo_db'
    
    with registry(db_name).cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        types = env['dl.salary.kpi.attendance.type'].search([('code', 'in', ['1LN', '0.5LN'])])
        print(f"Found types: {types.mapped('code')}")

if __name__ == "__main__":
    check()
