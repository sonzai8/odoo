import os
import sys

def verify():
    # Giả lập môi trường Odoo shell
    from odoo import api, SUPERUSER_ID
    from odoo.api import Environment
    import odoo
    
    # Kết nối registry
    db_name = 'odoo_db'
    registry = odoo.registry(db_name)
    
    with registry.cursor() as cr:
        env = Environment(cr, SUPERUSER_ID, {})
        Dossier = env['dl.wood.dossier']
        dossiers = Dossier.search([], limit=1)
        if not dossiers:
            print("No dossiers found in database to test!")
            return
            
        dossier = dossiers[0]
        print(f"Testing real rendering for dossier ID {dossier.id}: {dossier.name}")
        
        # Đảm bảo dossier có ít nhất 2 dòng sản phẩm để test merge
        if len(dossier.line_ids) < 2:
            print("Dossier has less than 2 lines. Creating a dummy line for testing...")
            species = env['dl.wood.species'].search([], limit=1)
            dossier.write({
                'line_ids': [(0, 0, {
                    'species_id': species.id if species else False,
                    'volume': 10.0,
                    'quantity': 10,
                })]
            })
            
        # Render HDSG
        docx_bytes = dossier._render_docx('hdsg')
        print(f"Rendered successfully, size: {len(docx_bytes)} bytes")
        
        # Lưu ra file test
        output_path = 'my_custom_addons/dl_wood_traceability/scratch/output_real_merged.docx'
        with open(output_path, 'wb') as f:
            f.write(docx_bytes)
        print(f"Saved real rendered docx to: {output_path}")
        
        # Kiểm tra cấu hình gộp ô của file thực tế
        import docx
        doc = docx.Document(output_path)
        table = doc.tables[0]
        print("\n--- Inspecting Table 0 of real rendered HDSG ---")
        for r_idx, row in enumerate(table.rows):
            cells = [c.text.strip().replace('\n', ' ') for c in row.cells]
            print(f"Row {r_idx}: {cells}")

if __name__ == '__main__':
    verify()
