# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class FilmMatrixViewer(models.TransientModel):
    _name = 'dl.film.matrix.viewer'
    _description = 'Ma trận Đơn giá HTML'

    html_content = fields.Html(string='Matrix', compute='_compute_html_content', sanitize=False)

    def _compute_html_content(self):
        for rec in self:
            pricelists = self.env['dl.film.pricelist'].search([('state', '=', 'confirmed')], order='year desc, month desc')
            if not pricelists:
                rec.html_content = "<div class='alert alert-warning'>Chưa có Bảng giá Ép Film nào được xác nhận.</div>"
                continue

            # In context, we might filter by a specific pricelist if opened from the form view
            target_ids = self.env.context.get('active_ids')
            if self.env.context.get('active_model') == 'dl.film.pricelist' and target_ids:
                pricelist = self.env['dl.film.pricelist'].browse(target_ids[0])
            else:
                pricelist = pricelists[0]

            import re
            lines = pricelist.line_ids
            # Thu thập các Ký hiệu độ dày (Rows) và tự động sắp xếp theo SỐ (vd: 9 ly đứng trước 12 ly)
            # Thu thập các Sản phẩm (Rows) và sắp xếp theo tên
            products = sorted(list(set(lines.mapped('product_tmpl_id'))), key=lambda x: x.name)
            
            # Thu thập các Cột (Brand + Surface)
            # Tạo dictionary lồng nhau: Brand -> [1m, 2m]
            brands = sorted(list(set(lines.mapped('x_film_brand_id'))), key=lambda x: x.name)
            
            # Gom dữ liệu để tra từ điển nhanh
            data_dict = {}
            for l in lines:
                key = (l.product_tmpl_id.id, l.x_film_brand_id.id, l.x_surface_type)
                data_dict[key] = l

            # Định dạng số tiền
            def format_money(amount):
                if not amount: return "-"
                return "{:,.0f}".format(amount).replace(',', '.')

            # CSS Styles
            css = """
            <style>
                .film-matrix-wrapper {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
                    padding: 20px;
                    background-color: #f9fafb;
                    border-radius: 8px;
                    color: #1e293b;
                }
                .film-matrix-container {
                    width: 100%;
                    overflow-x: auto;
                    margin-bottom: 40px;
                    background: #ffffff;
                    border: 1px solid #e1e7ec;
                    border-radius: 6px;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
                }
                .film-matrix-table {
                    width: 100%;
                    border-collapse: collapse;
                    min-width: 800px;
                    font-size: 14px;
                }
                .film-matrix-table th, .film-matrix-table td {
                    border: 1px solid #e2e8f0;
                    padding: 12px 16px;
                    text-align: center;
                    white-space: nowrap;
                }
                .film-matrix-table thead th {
                    background-color: #f8fafc;
                    font-weight: 600;
                    color: #475569;
                    text-transform: uppercase;
                    font-size: 13px;
                    letter-spacing: 0.5px;
                }
                .film-matrix-table tbody tr:hover {
                    background-color: #f1f5f9;
                }
                /* Freeze first column */
                .sticky-col {
                    position: sticky;
                    left: 0;
                    background-color: #f8fafc;
                    z-index: 10;
                    font-weight: bold;
                    border-right: 2px solid #cbd5e1 !important;
                    box-shadow: 2px 0 5px -2px rgba(0,0,0,0.1);
                }
                .film-matrix-table tbody th.sticky-col {
                    background-color: #ffffff;
                    color: #1e293b;
                }
                .film-matrix-table tbody tr:hover th.sticky-col {
                    background-color: #f1f5f9;
                }
                .cell-high { color: #15803d; font-weight: 500; }
                .cell-low { color: #b91c1c; font-weight: 400; }
                .cell-re { color: #0369a1; font-weight: 500; border-left: 1px dashed #cbd5e1; }
                .h-title {
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 15px;
                    margin-top: 10px;
                    color: #0f172a;
                    padding-left: 12px;
                    border-left: 4px solid #3b82f6;
                    display: flex;
                    align-items: center;
                }
                .brand-header {
                    border-bottom: 2px solid #cbd5e1 !important;
                    color: #334155 !important;
                    font-size: 14px !important;
                }
            </style>
            """

            # ==============================
            # BẢNG 1: GIÁ MỚI / GIÁ CŨ
            # ==============================
            html1 = f"""
            <link rel="stylesheet" href="/web/static/lib/bootstrap/css/bootstrap.css"/>
            <div class='film-matrix-wrapper'>
            <div class='h-title'><i class="fa fa-money mx-2"></i> 1. Bảng Đơn giá Chính (Mới / Cũ) - {pricelist.name}</div>
            <div class="film-matrix-container">
                <table class="film-matrix-table">
                    <thead>
                        <tr>
                            <th rowspan="2" class="sticky-col">Ký hiệu<br/>Độ dày</th>
            """
            for b in brands:
                html1 += f"<th colspan='4' class='brand-header'>{b.name}</th>"
            html1 += "</tr><tr>"
            for b in brands:
                html1 += "<th>1M (Mới)</th><th>1M (Cũ)</th><th>2M (Mới)</th><th>2M (Cũ)</th>"
            html1 += "</tr></thead><tbody>"

            for p in products:
                html1 += f"<tr><th class='sticky-col'>{p.name}</th>"
                for b in brands:
                    l_1m = data_dict.get((p.id, b.id, '1m'))
                    l_2m = data_dict.get((p.id, b.id, '2m'))
                    
                    p1_h = format_money(l_1m.price_high) if l_1m else "-"
                    p1_l = format_money(l_1m.price_low) if l_1m else "-"
                    p2_h = format_money(l_2m.price_high) if l_2m else "-"
                    p2_l = format_money(l_2m.price_low) if l_2m else "-"
                    
                    html1 += f"<td class='cell-high'>{p1_h}</td><td class='cell-low'>{p1_l}</td>"
                    html1 += f"<td class='cell-high'>{p2_h}</td><td class='cell-low'>{p2_l}</td>"
                html1 += "</tr>"
            html1 += "</tbody></table></div>"

            # ==============================
            # BẢNG 2: GIÁ ÉP LẠI
            # ==============================
            html2 = f"""
            <div class='h-title'><i class="fa fa-refresh mx-2"></i> 2. Bảng Đơn giá Ép Lại - {pricelist.name}</div>
            <div class="film-matrix-container">
                <table class="film-matrix-table">
                    <thead>
                        <tr>
                            <th rowspan="2" class="sticky-col">Ký hiệu<br/>Độ dày</th>
            """
            for b in brands:
                html2 += f"<th colspan='2' class='brand-header'>{b.name}</th>"
            html2 += "</tr><tr>"
            for b in brands:
                html2 += "<th>1M (Sửa Mới)</th><th>1M (Sửa Cũ)</th><th>2M (Sửa Mới)</th><th>2M (Sửa Cũ)</th>"
            html2 += "</tr></thead><tbody>"

            for p in products:
                html2 += f"<tr><th class='sticky-col'>{p.name}</th>"
                for b in brands:
                    l_1m = data_dict.get((p.id, b.id, '1m'))
                    l_2m = data_dict.get((p.id, b.id, '2m'))
                    
                    pr1_h = format_money(l_1m.price_re_ep_high) if l_1m else "-"
                    pr1_l = format_money(l_1m.price_re_ep_low) if l_1m else "-"
                    pr2_h = format_money(l_2m.price_re_ep_high) if l_2m else "-"
                    pr2_l = format_money(l_2m.price_re_ep_low) if l_2m else "-"
                    
                    html2 += f"<td class='cell-re'>{pr1_h}</td><td class='cell-low'>{pr1_l}</td>"
                    html2 += f"<td class='cell-re'>{pr2_h}</td><td class='cell-low'>{pr2_l}</td>"
                html2 += "</tr>"
            html2 += "</tbody></table></div></div>"

            rec.html_content = css + html1 + html2
