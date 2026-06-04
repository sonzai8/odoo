import logging

_logger = logging.getLogger(__name__)

def clean_all_data(env):
    try:
        print("Bắt đầu force-xoá dữ liệu...")
        from odoo import models
        
        # Lệnh sản xuất
        production_orders = env['dl.wood.production.order'].sudo().with_context(active_test=False).search([])
        count_po = len(production_orders)
        if count_po:
            models.Model.unlink(production_orders)
            print(f"Đã force-xoá {count_po} Lệnh Sản Xuất.")
            
        # Đơn bán hàng
        sale_orders = env['sale.order'].sudo().with_context(active_test=False).search([])
        count_so = len(sale_orders)
        if count_so:
            models.Model.unlink(sale_orders)
            print(f"Đã force-xoá {count_so} Đơn Bán Hàng.")
            
        # Sản phẩm gỗ
        products = env['product.template'].sudo().with_context(active_test=False).search([('is_wood_product', '=', True)])
        count_prod = len(products)
        if count_prod:
            variants = env['product.product'].sudo().with_context(active_test=False).search([('product_tmpl_id', 'in', products.ids)])
            models.Model.unlink(variants)
            models.Model.unlink(products)
            print(f"Đã force-xoá {count_prod} Sản phẩm Gỗ.")
            
        env.cr.commit()
        print("HOÀN TẤT XOÁ DỮ LIỆU!")
        
    except Exception as e:
        env.cr.rollback()
        print(f"Có lỗi xảy ra: {str(e)}")

clean_all_data(env)
