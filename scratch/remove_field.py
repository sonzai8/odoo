import sys
import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', 'odoo.conf', '-d', 'odoo_db_production'])
registry = odoo.registry('odoo_db_production')

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    field = env['ir.model.fields'].search([('model', '=', 'res.partner'), ('name', '=', 'x_private_name')])
    if field:
        print("Found field, deleting:", field)
        field.unlink()
        print("Deleted.")
    else:
        print("Field not found in ir.model.fields.")
