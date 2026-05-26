import os

# Tìm tất cả file attachments có lưu trong filestore
attachments = env['ir.attachment'].search([('store_fname', '!=', False)])

filestore = odoo.tools.config.filestore('odoo_db_production')

missing = []
for att in attachments:
    full_path = os.path.join(filestore, att.store_fname)
    if not os.path.exists(full_path):
        missing.append(att)

print(f"Tìm thấy {len(missing)} attachments bị thiếu file vật lý.")
if missing:
    for att in missing:
        print(f"Xóa attachment ID {att.id} (name: {att.name}, fname: {att.store_fname})")
        try:
            att.unlink()
        except Exception as e:
            print(f"Lỗi khi xóa bằng ORM: {e}, thử xóa bằng SQL...")
            env.cr.execute("DELETE FROM ir_attachment WHERE id = %s", (att.id,))
    
    env.cr.commit()
    print("Đã xóa xong các attachment lỗi.")
else:
    print("Không có attachment nào bị lỗi.")
