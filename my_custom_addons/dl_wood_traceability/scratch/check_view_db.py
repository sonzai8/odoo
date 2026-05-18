import sys
sys.path.append('/Users/sonzai/dev/odoo 19/odoo')
import odoo
from odoo import api, tools

tools.config.parse_config(['-c', 'odoo.conf'])

registry = odoo.modules.registry.Registry('odoo_db')
with registry.cursor() as cr:
    env = api.Environment(cr, odoo.SUPERUSER_ID, {})
    view = env['ir.ui.view'].search([('name', '=', 'dl.wood.production.order.form')], limit=1)
    if view:
        print("=== XML VIEW IN DATABASE ===")
        print(view.arch_db)
    else:
        print("VIEW NOT FOUND IN DATABASE!")
