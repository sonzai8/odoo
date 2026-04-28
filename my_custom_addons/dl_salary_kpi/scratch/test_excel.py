import sys
import os

# Setup Odoo environment
sys.path.append('/Users/sonzai/dev/odoo 19/odoo')
import odoo
from odoo.tools import config
config.parse_config(['-c', '/Users/sonzai/dev/odoo 19/odoo/odoo.conf'])
odoo.cli.server.setup_server(config)
registry = odoo.registry(config['db_name'])

with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    # Get the latest month
    month = env['dl.salary.kpi.month'].search([], limit=1)
    if month:
        print(f"Testing export for {month.name}...")
        try:
            res = month.action_export_salary_report()
            print("Export successful, returned:", res)
            # Find the attachment
            attachment_id = int(res['url'].split('/web/content/')[1].split('?')[0])
            attachment = env['ir.attachment'].browse(attachment_id)
            import base64
            with open('test_output.xlsx', 'wb') as f:
                f.write(base64.b64decode(attachment.datas))
            print("Saved as test_output.xlsx")
        except Exception as e:
            print("Export failed:", str(e))
    else:
        print("No month record found.")
