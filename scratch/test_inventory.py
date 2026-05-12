import xmlrpc.client
url = 'http://localhost:8069'
db = 'odoo_db'
username = 'admin'
password = 'c59bc5cb4f2c64bce3d9cc870537f83dff4669ba'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
# Gọi action_confirm cho phiếu ID 3
res = models.execute_kw(db, uid, password, 'dl.wood.dossier.inventory', 'action_confirm', [[3]])
print(f"Result: {res}")

# Kiểm tra tồn kho dossier 1161
dossier = models.execute_kw(db, uid, password, 'dl.wood.dossier', 'read', [[1161]], {'fields': ['name', 'remaining_qty']})
print(f"Dossier: {dossier}")

# Kiểm tra ledger
ledgers = models.execute_kw(db, uid, password, 'dl.dossier.ledger', 'search_read', [[['inventory_id', '=', 3]]], {'fields': ['actual_qty', 'note', 'state']})
print(f"Ledgers: {ledgers}")
