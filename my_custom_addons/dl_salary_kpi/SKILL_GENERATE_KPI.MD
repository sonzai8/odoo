# SKILL: Tự Động Sinh Điểm KPI Cân Đối Lương (Auto Generate KPI)

## 1. Ngữ cảnh (Context & Business Rule)
Tại công ty Sản xuất Gỗ Đức Lâm, tồn tại khái niệm "Lương nội bộ" (Tổng thu nhập thực tế) thường cao hơn "Lương tính KPI".
Hệ thống cần tự động sinh ra một số Điểm KPI (từ 50 đến 70) để số Tiền KPI sinh ra tiệm cận mức Lương nội bộ. Số tiền chênh lệch còn thiếu sẽ được trả bằng Tiền mặt.

**Ràng buộc cốt lõi:** 
- **Tiền mặt (Cash):** BẮT BUỘC phải là số tròn đến hàng **chục nghìn (10.000 VNĐ)** để thuận tiện chi trả thực tế.
- **Điểm KPI có thể lẻ (Float):** Hệ thống hỗ trợ điểm lẻ (2 chữ số thập phân) để hấp thụ phần lẻ từ việc làm tròn Tiền mặt, đảm bảo tổng thu nhập không đổi.
- **Phân bổ tỷ lệ thuận:** Các tiêu chí KPI phải tỷ lệ với điểm tối đa của chúng.

## 2. Công thức toán học (Reverse Engineering)
Tuyệt đối tuân thủ thuật toán suy ngược sau đây:
- Hệ số KPI = `1 + (Điểm KPI - 50) / 50`
- Tỷ lệ hưởng = `Hệ số KPI - 1` = `(Điểm KPI - 50) / 50`
- Tiền KPI tối đa (khi Điểm KPI = 70) = `Lk * 0.4`
- Tiền mặt tối thiểu = `Ln - Lk - Tiền KPI tối đa`
*(Trong đó: Ln là Lương nội bộ, Lk là Lương cơ bản tính KPI)*

## 3. Mapping Model Dữ liệu (dl.salary.kpi.line)
- `payroll_internal_salary` (Monetary): Lương nội bộ mục tiêu (Ln).
- `payroll_net_salary_base` (Monetary): Lương tính KPI (Lk) - Là Thực lĩnh ngoài sau thuế/bảo hiểm.
- `payroll_kpi_score` (Float): Điểm KPI (Generated).
- `payroll_kpi_amount` (Monetary): Tiền KPI (Generated).
- `payroll_cash_amount` (Monetary): Tiền mặt cần trả thêm (Generated).

## 4. Thuật toán Phân rã Tiêu chí (Proportional Distribution)
Điểm KPI tổng (`p_final`) được chia vào 5 tiêu chí theo nguyên tắc tỷ lệ thuận:
- **C1 (Năng suất):** Max 40 (Gánh toàn bộ phần lẻ thập phân).
- **C2 (Kỷ luật):** Max 30 (Số nguyên).
- **C3 (Nhóm):** Max 15 (Số nguyên).
- **C4 (5S):** Max 10 (Số nguyên).
- **C5 (Tiết kiệm):** Max 5 (Số nguyên).

**Nguyên tắc:** 
1. Tính C2-C5 là số nguyên bằng cách: `round(Max_i * (p_final / 100) * ngẫu nhiên)`.
2. Tính C1 bằng: `p_final - sum(C2..C5)`.
3. Nếu C1 vượt Max 40, đẩy phần dư sang các tiêu chí khác dưới dạng số nguyên.

## 5. Thuật toán Gen KPI (Python Logic)
Hàm `action_generate_kpi_scores()` trong `dl.salary.kpi.line` thực hiện:
1. Tính `p_final` để bù đắp khoảng cách `Ln - Lk`.
2. Nếu khoảng cách quá lớn, sử dụng Tiền mặt (ưu tiên > 1 triệu).
3. Sử dụng chuẩn hóa để chia `p_final` vào C1-C5.
4. Làm tròn 2 chữ số thập phân cho mọi điểm số.