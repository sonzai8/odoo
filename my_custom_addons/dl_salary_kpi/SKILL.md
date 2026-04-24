# SKILL.md — dl_salary_kpi

> File này là entry point nhanh. Chi tiết đầy đủ nằm trong hệ thống Knowledge Items.

## Quick Reference

| Mục | Vị trí |
|---|---|
| **Kiến trúc module** | `~/.gemini/antigravity/knowledge/dl-salary-kpi-architecture/` |
| **Quy chế thưởng (QĐ 3108/2025)** | `~/.gemini/antigravity/knowledge/dl-bonus-policy/` |
| **UI Patterns & Lỗi thường gặp** | `~/.gemini/antigravity/knowledge/odoo19-ui-patterns/` |
| **Workflow phát triển** | `~/.gemini/antigravity/knowledge/odoo19-dev-workflow/` |

## Lệnh nhanh

```bash
# Upgrade module (XML/Data)
python3 odoo-bin -c odoo.conf -u dl_salary_kpi -d odoo_db --stop-after-init

# Start dev server (Python → phải restart)
python3 odoo-bin -c odoo.conf --dev=all
```

## Điều quan trọng nhất cần nhớ

1. **Thêm method Python mới** → BẮT BUỘC restart server (kill cũ + start lại)
2. **Inline filter cho One2many** → Dùng computed field + inverse, KHÔNG dùng domain
3. **Action button trong form** → Return `True` để giữ nguyên tab, KHÔNG return reload
4. **Chặn xóa bản ghi** → Override `unlink()` với kiểm tra `state != 'draft'`
5. **Layout 2 cột** → Dùng flexbox + `min-width: 0` + `pointer-events: none` cho cột chỉ xem
