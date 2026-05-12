import xmlrpc.client
url = 'http://localhost:8069'
db = 'odoo_db'
username = 'admin'
password = 'c59bc5cb4f2c64bce3d9cc870537f83dff4669ba'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# 1. Tạo phiếu mới
inv_id = models.execute_kw(db, uid, password, 'dl.wood.dossier.inventory', 'create', [{
    'line_ids': [[0, 0, {'dossier_id': 1161, 'real_qty': 50}]],
    'note': 'Test unlink v2'
}])
print(f"Created Inventory ID: {inv_id}")

# 2. Xác nhận
models.execute_kw(db, uid, password, 'dl.wood.dossier.inventory', 'action_confirm', [[inv_id]])
dossier = models.execute_kw(db, uid, password, 'dl.wood.dossier', 'read', [[1161]], {'fields': ['remaining_qty']})
print(f"Stock after confirm: {dossier[0]['remaining_qty']}")

# 3. Xóa
print(f"Unlinking Inventory ID: {inv_id}...")
models.execute_kw(db, uid, password, 'dl.wood.dossier.inventory', 'unlink', [[inv_id]])

# 4. Kiểm tra tồn kho (phải quay lại số cũ trước khi trừ)
dossier = models.execute_kw(db, uid, password, 'dl.wood.dossier', 'read', [[1161]], {'fields': ['remaining_qty']})
print(f"Stock after unlink: {dossier[0]['remaining_qty']}")

# 5. Kiểm tra ledger
ledgers = models.execute_kw(db, uid, password, 'dl.dossier.ledger', 'search_read', [[['dossier_id', '=', 1161]]], {'fields': ['actual_qty', 'note'], 'order': 'id desc', 'limit': 2})
print(f"Latest Ledgers: {ledgers}")
