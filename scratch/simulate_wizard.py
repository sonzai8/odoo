import xmlrpc.client

url = 'http://localhost:8069'
db = 'odoo_db_production'
username = 'admin'
password = '1'

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

# 1. Tìm 1 dossier line
line_ids = models.execute_kw(db, uid, password, 'dl.wood.dossier.line', 'search', [[]], {'limit': 1})
if line_ids:
    line_id = line_ids[0]
    # 2. Tạo wizard
    wizard_id = models.execute_kw(db, uid, password, 'dl.wood.peeling.line.production.wizard', 'create', [{
        'dossier_line_id': line_id,
        'volume_wood': 1.0,
        'yield_factor': 1.4,
        'peeling_variant_id': 1, # Fake, có thể lỗi constraint
    }])
    print("Wizard created:", wizard_id)
    # 3. Chạy action_confirm
    try:
        res = models.execute_kw(db, uid, password, 'dl.wood.peeling.line.production.wizard', 'action_confirm', [[wizard_id]])
        print("Success:", res)
    except Exception as e:
        print("Error:", e)

