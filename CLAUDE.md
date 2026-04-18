# Odoo 19 Development Protocol - Plywood & Payroll System

## Project Context
- **Industry:** Sản xuất gỗ dán (Plywood Production).
- **Core Custom Modules:** `dl_wood_payroll`, `dl_wood_production`.
- **Environment:** Python 3.12+, Odoo 19.0 Community/Enterprise.
- **Infrastructure:** Docker containers trên Windows WSL2.

## Tech Stack & Architecture
- **Backend:** Python 3.12.7 (Strict typing encouraged).
- **Database:** PostgreSQL (ORM-first, no raw SQL unless optimized queries).
- **Frontend:** OWL (Odoo Web Library) Framework, XML Views.
- **Structure:** Tuân thủ kiến trúc Odoo MVC (Models, Views, Controllers).

## Coding Standards
### Python (Models & Logic)
- **Inheritance:** Luôn sử dụng `_inherit` để mở rộng module gốc. Không sửa core.
- **Naming:** - Class: `PascalCase` (ví dụ: `DlWoodPayroll`).
  - Fields/Methods: `snake_case`.
  - Fields chuyên biệt gỗ dán: `thickness`, `layers`, `glue_type`, `film_coated`.
- **Formatting:** Tuân thủ PEP8. Sử dụng type hinting cho các hàm xử lý lương/chi phí.
- **ORM:** Ưu tiên `filtered()`, `mapped()`, `sorted()`. Hạn chế loop qua recordset lớn.

### XML (Views & Security)
- **ID Naming:** `model_name_view_type` (ví dụ: `view_dl_payroll_form`).
- **XPath:** Sử dụng `expr` cụ thể, hạn chế dùng chỉ số mảng (index) để tránh lỗi khi update.
- **Security:** Mọi model mới phải có khai báo trong `ir.model.access.csv`.

### OWL (Frontend)
- Sử dụng cấu trúc Component-based.
- Toàn bộ JS/SCSS phải nằm trong `static/src/`.

## Essential Commands
- **Restart Odoo:** `docker restart <container_name>`
- **Update Module:** `odoo -u dl_wood_payroll,dl_wood_production -d <db_name> --stop-after-init`
- **Scaffold New Module:** `odoo scaffold <name> /extra-addons/`
- **Shell Access:** `odoo shell -d <db_name>`

## Domain-Specific Knowledge (Plywood)
- **Attributes:** Khi tính toán BoM (Bill of Materials), lưu ý các thuộc tính: Độ dày (thickness), Loại phim (film coating), Loại gỗ cốt.
- **Payroll:** Logic tính lương cần căn cứ vào sản lượng công nhân (piece-rate) dựa trên các công đoạn sản xuất gỗ.

## Safety & Performance Rails
- Không bao giờ commit file `.pyc`, `__pycache__` hoặc dữ liệu rác vào Git.
- Kiểm tra tính toàn vẹn của file `__manifest__.py` trước khi hướng dẫn cài đặt.
- Khi viết hàm tính toán (`@api.depends`), luôn đảm bảo xử lý trường hợp giá trị `False` hoặc `None` để tránh lỗi Server.

- BẮT BUỘC: Mọi thẻ `<template>`, `<record>`, `<menuitem>` phải được bọc bên trong thẻ `<data>...</data>`. Không được để thẻ trần dưới `<odoo>`.
- Không sử dụng thuộc tính `url` trực tiếp trong `<menuitem>`. Khi cần link tới trang web/controller, bắt buộc phải định nghĩa qua `ir.actions.act_url`.
- Trong QWeb template, sử dụng `json.dumps()` thay vì `json()` để convert Python dict sang JS object.