# Run this with odoo shell
import logging
_logger = logging.getLogger(__name__)

peeling_ids = env['dl.wood.peeling.dossier'].search([])
if peeling_ids:
    peeling_ids.unlink()
    print(f"Đã xoá {len(peeling_ids)} hồ sơ ván bóc.")

dossier_ids = env['dl.wood.dossier'].search([])
if dossier_ids:
    for d in dossier_ids:
        d.write({'state': 'draft'}) # Bypass constraints if any
    dossier_ids.unlink()
    print(f"Đã xoá {len(dossier_ids)} hồ sơ gỗ.")

env.cr.commit()
print("Hoàn tất xoá dữ liệu.")
