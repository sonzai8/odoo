import odoo
from odoo import api, registry

def delete_types():
    config_file = '/Users/sonzai/dev/odoo 19/odoo/odoo.conf'
    odoo.tools.config.parse_config(['-c', config_file])
    db_name = 'odoo_db'
    
    # Manually initialize registry if needed, or just use the existing one
    reg = registry(db_name)
    with reg.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        types = env['dl.salary.kpi.attendance.type'].search([('code', 'in', ['1LN', '0.5LN'])])
        if types:
            print(f"Deleting types: {types.mapped('code')}")
            types.unlink()
            cr.commit()
        else:
            print("No types to delete.")

if __name__ == "__main__":
    delete_types()
