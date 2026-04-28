# SKILL.md — dl_salary_kpi

## Excel Template: TEMPLATE_2026.xlsx

### Quy tắc xử lý
1. **Dòng Master (Dòng 8):** Luôn dùng dòng 8 làm mẫu để sao chép Style (Font, Border, Fill), Formula và Chiều cao dòng cho tất cả nhân viên.
2. **Dịch công thức:** Sử dụng `Translator` để tịnh tiến công thức từ dòng 8 xuống dòng N.
3. **Ghi dữ liệu an toàn:** Luôn dùng hàm `safe_write` để bỏ qua các ô gộp (MergedCell) bị read-only.
4. **Vùng bảo vệ (AT -> BX):** Tuyệt đối không ghi đè dữ liệu vào vùng này vì chứa công thức tính toán tự động của Excel.

### Mapping Dữ liệu (Dòng 8+)
| Cột | Dữ liệu | Định dạng/Ghi chú |
|---|---|---|
| **A (1)** | Số thứ tự | `STT` (1, 2, 3...) |
| **B (2)** | Mã số thuế | `line.employee_id.dl_tax_id` |
| **C (3)** | Họ và tên | `line.employee_id.name` |
| **D (4)** | Ngày sinh | `dd/mm/yyyy` |
| **E (5)** | Số CCCD | `line.employee_id.identification_id` |
| **F (6)** | Giới tính | `Nam` / `Nữ` |
| **G (7)** | Phòng ban | `line.employee_id.dl_tax_department_id.name` |
| **H (8)** | Chức vụ | `line.employee_id.dl_tax_position` |
| **I (9)** | Lương cơ bản | `line.employee_id.dl_tax_base_salary` |
| **J -> AN (10-40)** | Công thường | Mã chấm công ngày 01-31 |
| **AT -> BX (46-76)** | OT | Công làm thêm. Chỉ ghi đè mã chấm công làm thêm vào các ngày Chủ nhật (T2-T7 để nguyên cho công thức chạy). |
| **CQ (95)** | Trợ cấp phụ nữ | Lấy ở cấu hình chung (chỉ Nữ) |
| **CR (96)** | Trợ cấp ăn ca | Lấy ở cấu hình chung |
| **DG (111)** | Lương KPI | (Tạm thời để trống) |
| **EE (135)** | Thưởng cố định năm | `line.payroll_annual_bonus` |
| **EH (138)** | Người phụ thuộc | Tổng số NPT của nhân viên đang active |

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
