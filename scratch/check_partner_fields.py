# -*- coding: utf-8 -*-
import odoo
from odoo import api, SUPERUSER_ID

def check_required_fields():
    registry = odoo.registry('odoo_db')
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        Partner = env['res.partner']
        
        required_fields = []
        for name, field in Partner._fields.items():
            if field.required:
                required_fields.append(name)
        
        print("Required fields in model:")
        print(required_fields)
        
        # Check if it's a view requirement
        View = env['ir.ui.view']
        view_id = env.ref('base.view_partner_form').id
        # This is harder to check via script without rendering
        
if __name__ == "__main__":
    check_required_fields()
