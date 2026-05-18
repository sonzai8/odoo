# -*- coding: utf-8 -*-
import sys
sys.path.append('/Users/sonzai/dev/odoo 19/odoo')
import odoo
from odoo import api, tools

tools.config.parse_config(['-c', 'odoo.conf'])

def inspect_uoms():
    registry = odoo.modules.registry.Registry('odoo_db')
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        fields = env['product.template']._fields.keys()
        uom_fields = [f for f in fields if 'uom' in f or 'unit' in f]
        print("=== UOM/UNIT FIELDS IN PRODUCT.TEMPLATE ===")
        print(uom_fields)

if __name__ == '__main__':
    inspect_uoms()
