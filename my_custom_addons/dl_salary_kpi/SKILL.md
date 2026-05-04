# SKILL.md — dl_salary_kpi

> File này là entry point nhanh cho các kỹ năng (Skills) cốt lõi của hệ thống. Chi tiết đầy đủ nằm trong hệ thống Knowledge Items.

---

## 1. EXCEL MAPPING (TEMPLATE_2026.xlsx)
*Tài liệu tham chiếu chính cho logic Xuất báo cáo lương.*

### Quy tắc kỹ thuật
1. **Dòng Master (Dòng 8):** Phải copy dòng 8 để lấy định dạng (Style) và công thức trước khi ghi dữ liệu.
2. **Dịch công thức (Translator):** Tịnh tiến công thức từ dòng 8 xuống dòng N (ví dụ: `=SUM(I8:AM8)` -> `=SUM(I9:AM9)`).
3. **Ghi dữ liệu an toàn:** Kiểm tra `MergedCell` để tránh ghi vào các ô phụ (read-only), chỉ ghi vào ô master.

### Mapping tọa độ
| Vùng | Cột | Nội dung | Ghi chú |
|---|---|---|---|
| **Header** | A3, F4, K4, O4 | Thông tin chung | Tháng/Năm, Doanh thu... |
| **Nhân sự** | B -> I | Thông tin nhân viên | Họ tên, MST, Ngày sinh, Lương CB... |
| **J -> AN (10-40)** | Công thường | Mã chấm công ngày 01-31 | Ghi mã N, Đ, P, PL... |
| **AT -> BX (46-76)** | OT | Công làm thêm | **Chỉ ghi vào ngày Chủ nhật**. |
| **CP, CQ** | Trợ cấp | Phụ nữ, Ăn ca | Lấy từ cấu hình tháng. |
| **DG (111)** | KPI | Tiền KPI cân đối | — |
| **DP (120)** | Thuế TNCN | Số tiền thuế phải đóng | Kết quả đồng bộ từ Odoo. |
| **EI (139)** | Người phụ thuộc | Số lượng NPT | — |

---

## 2. KỸ NĂNG: TÍNH THUẾ THU NHẬP CÁ NHÂN (PIT LOGIC)
*Áp dụng từ tháng 04/2026.*

### Định mức cấu hình (Constants)
- **Giảm trừ bản thân:** 15,500,000 VNĐ
- **Giảm trừ người phụ thuộc:** 6,200,000 VNĐ / người
- **Miễn thuế tiền ăn:** Theo thực tế (ví dụ: 650,000 VNĐ)

### Quy trình 4 bước
1. **B1: Tính Thu nhập chịu thuế (TNCT)**
   `TNCT = Tổng thu nhập thực tế - Miễn thuế tiền ăn + Lương trả cho ngày không nghỉ phép`
2. **B2: Tính Tổng giảm trừ**
   `Tổng giảm trừ = Bảo hiểm bắt buộc + Giảm trừ bản thân + (Số NPT * Giảm trừ NPT)`
3. **B3: Tính Thu nhập tính thuế (TNTT)**
   `TNTT = TNCT - Tổng giảm trừ`. Nếu `TNTT <= 0` thì Thuế = 0.
4. **B4: Biểu thuế lũy tiến 5 bậc**
   - **Bậc 1:** TNTT <= 10M -> `Tax = TNTT * 0.05`
   - **Bậc 2:** TNTT <= 30M -> `Tax = (TNTT * 0.10) - 500,000`
   - **Bậc 3:** TNTT <= 60M -> `Tax = (TNTT * 0.20) - 3,500,000`
   - **Bậc 4:** TNTT <= 100M -> `Tax = (TNTT * 0.30) - 9,500,000`
   - **Bậc 5:** TNTT > 100M -> `Tax = (TNTT * 0.35) - 14,500,000`

### Ràng buộc
- Làm tròn kết quả về số nguyên (0 chữ số thập phân).
- Các định mức phải lấy từ cấu hình (`res.company`), không được hardcode.

---

## 3. KỸ NĂNG: TỰ ĐỘNG SINH KPI (AUTO GENERATE KPI)
*Cân đối Lương nội bộ (Ln) thông qua Điểm KPI và Tiền mặt.*

### Thuật toán cốt lõi
1. **Lk (Lương tính KPI):** Lấy từ `payroll_net_salary_base`.
2. **Tiền mặt (Cash):** `max(0, Ln - Lk - (Lk * 0.4))`. Ưu tiên >= 1.000.000 VNĐ.
3. **Điểm KPI (p):** `50 + (50 * Mk / Lk)`, giới hạn [50, 70], hỗ trợ số lẻ.
4. **Phân bổ tiêu chí:** Phân bổ `p` vào C1-C5 tỷ lệ thuận. C2-C5 là số nguyên, C1 gánh phần lẻ.

Chi tiết hướng dẫn kỹ thuật xem tại [SKILL_GENERATE_KPI.MD](file:///Users/sonzai/dev/odoo%2019/odoo/my_custom_addons/dl_salary_kpi/SKILL_GENERATE_KPI.MD).
