# SKILL: Tự Động Sinh Điểm KPI Cân Đối Lương (Auto Generate KPI)

## 1. Ngữ cảnh (Context & Business Rule)
Tại công ty Sản xuất Gỗ Đức Lâm, tồn tại khái niệm "Lương nội bộ" (Tổng thu nhập thực tế) thường cao hơn "Lương tính KPI".
Hệ thống cần tự động sinh ra một số Điểm KPI (từ 50 đến 70) để số Tiền KPI sinh ra tiệm cận mức Lương nội bộ. Số tiền chênh lệch còn thiếu sẽ được trả bằng Tiền mặt.
**Ràng buộc cốt lõi:** Tiền mặt trả thêm BẮT BUỘC phải là số chẵn (làm tròn lên bội số của 10.000 VNĐ). Tiền KPI có thể lẻ.

## 2. Công thức toán học (Reverse Engineering)
Tuyệt đối tuân thủ thuật toán suy ngược sau đây:
- Hệ số KPI = `1 + (Điểm KPI - 50) / 50`
- Tỷ lệ hưởng = `Hệ số KPI - 1` = `(Điểm KPI - 50) / 50`
- Tiền KPI tối đa (khi Điểm KPI = 70) = `Lk * 0.4`
- Tiền mặt tối thiểu = `Ln - Lk - Tiền KPI tối đa`
*(Trong đó: Ln là Lương nội bộ, Lk là Lương cơ bản tính KPI)*

## 3. Mapping Model Dữ liệu (dl.salary.kpi.line)
- `payroll_internal_salary` (Monetary): Lương nội bộ mục tiêu (Ln).
- `payroll_net_salary` (Monetary): Lương tính KPI (Lk) - Là Thực lĩnh tạm tính sau khi đã trừ các khoản khấu trừ Bảo hiểm và Thuế TNCN.
- `payroll_kpi_score` (Float): Điểm KPI (Generated).
- `payroll_kpi_amount` (Monetary): Tiền KPI (Generated).
- `payroll_cash_amount` (Monetary): Tiền mặt cần trả thêm (Generated).

## 4. Xây dựng Import Wizard
Cập nhật `dl.salary.kpi.import.wizard` để Import Lương nội bộ:
- **Cấu trúc File Excel mẫu (Import Lương nội bộ):**
  - Cột A: STT.
  - Cột B: Số CCCD (Mã định danh chính).
  - Cột C: Họ và Tên.
  - Cột D: Bộ phận.
  - Cột E: Số công (Mặc định 0).
  - Cột F: Lương nội bộ (Ln).
- **Logic Mapping:** Tìm kiếm dòng lương (`dl.salary.kpi.line`) có `identification_id` khớp với Cột B trong cùng một tháng bảng công.

## 5. Thuật toán Gen KPI (Python Logic)
Viết hàm `action_generate_kpi_scores()` trong `dl.salary.kpi.line`:

```python
import math

# Constant
ROUND_UNIT = 10000

def action_generate_kpi_scores(self):
    for rec in self:
        ln = rec.payroll_internal_salary
        lk = rec.tax_base_salary
        
        # Bỏ qua nếu không có Lương nội bộ hoặc Lương tính KPI = 0
        if not ln or lk <= 0:
            continue
            
        max_kpi_amount = lk * 0.4
        min_cash = ln - lk - max_kpi_amount
        
        # 1. Lk (Thực lĩnh cơ sở): Lương thực lĩnh tạm tính sau thuế/bảo hiểm.
        # 2. p_float (Điểm KPI lý thuyết): 50 + (50 * (Ln - Lk) / Lk).
        # 3. p_int (Điểm KPI chốt): floor(p_float), giới hạn [50, 70].
        # 4. Mk (Tiền KPI thực tế): Lk * (p_int - 50) / 50.
        # 5. Cash (Tiền mặt): Ln - Lk - Mk.
        # Ghi chú: Điểm KPI luôn là số nguyên. Tiền mặt sẽ gánh phần lẻ thập phân để đảm bảo Tổng thực lĩnh khớp đúng Ln.
        
        p_float = 50 + (50 * (ln - lk) / lk)
        p = math.floor(p_float)
        
        # Đảm bảo giới hạn an toàn [50, 70]
        if p > 70: p = 70
        if p < 50: p = 50
        
        mk = lk * (p - 50) / 50
        cash = ln - lk - mk
        
        # Cập nhật kết quả
        rec.payroll_kpi_score = p
        rec.payroll_kpi_amount = mk
        rec.payroll_cash_amount = cash
```