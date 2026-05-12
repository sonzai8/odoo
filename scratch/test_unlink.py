import xmlrpc.client
url = 'http://localhost:8069'
db = 'odoo_db'
username = 'admin'
password = 'c59bc5cb4f2c64bce3d9cc870537f83dff4669ba'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# 1. Kiểm tra tồn kho hiện tại hồ sơ 1161 (đang là 80)
dossier = models.execute_kw(db, uid, password, 'dl.wood.dossier', 'read', [[1161]], {'fields': ['remaining_qty']})
print(f"Stock before unlink: {dossier[0]['remaining_qty']}")

# 2. Xóa phiếu kiểm kê ID 3 (phiếu này đã xác nhận làm giảm từ 113 -> 80)
print("Unlinking inventory ID 3...")
models.execute_kw(db, uid, password, 'dl.wood.dossier.inventory', 'unlink', [[3]])

# 3. Kiểm tra lại tồn kho (phải quay lại 113)
dossier = models.execute_kw(db, uid, password, 'dl.wood.dossier', 'read', [[1161]], {'fields': ['remaining_qty']})
print(f"Stock after unlink: {dossier[0]['remaining_qty']}")

# 4. Kiểm tra ledger xem có bản ghi "Hoàn trả" không
ledgers = models.execute_kw(db, uid, password, 'dl.dossier.ledger', 'search_read', [[['dossier_id', '=', 1161]]], {'fields': ['actual_qty', 'note'], 'order': 'id desc', 'limit': 2})
print(f"Latest Ledgers: {ledgers}")
