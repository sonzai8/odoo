# KI: Thuật Toán Cân Đối Lương - KPI & Sửa Nhanh Dữ Liệu Bất Thường

Tài liệu này ghi chú lại (Knowledge Item) toàn bộ logic và bối cảnh (context) của bài toán Cân đối KPI và Công cụ Sửa nhanh trong hệ thống Lương Sản Xuất Đức Lâm.

## 1. Bài Toán & Bối Cảnh (Context)
- Nhân viên Xưởng Sản xuất thường có một mức Lương Thỏa Thuận Nội Bộ (Ln) được cam kết cố định theo tháng (hoặc công nhật).
- Trong khi đó, việc chấm công được thực hiện theo số ngày thực tế làm việc, có làm thêm, có phụ cấp, sinh ra mức Thực Lĩnh Ngoài (Lk).
- Để khớp được **Ln = Lk + Tiền thưởng KPI + Tiền Mặt**, kế toán mất rất nhiều thời gian cân đối thủ công.
- Thuật toán tự động sinh ra Điểm KPI và gán số Tiền Mặt dôi dư sao cho bảng lương luôn khớp từng đồng.

## 2. Logic Cân Đối KPI Ngẫu Nhiên (`action_generate_kpi_scores`)
**Vị trí:** `dl_salary_kpi_line.py`

### Quy tắc cốt lõi:
1. **Tiền mặt phải có ý nghĩa:** Nếu đã phát sinh chi Tiền mặt (Cash_needed > 0), số Tiền mặt tối thiểu phải >= `1.000.000đ` (tránh tình trạng đi rút ngân hàng vài trăm nghìn lẻ để phát cho công nhân).
2. **Điểm KPI tự nhiên:** Không ép điểm KPI lên kịch kim `70` để trông khách quan.
    - Nếu dư địa lớn: Điểm KPI được random trong khoảng [50, 70].
    - **Quy tắc ưu tiên (Mới):** Hệ thống ưu tiên rơi vào khoảng **60 - 70 điểm** (xác suất 70%) để số liệu trông tích cực hơn, 30% còn lại rơi vào khoảng 50 - 60.
    - Nếu dư địa hẹp (Ln - Lk sát 1tr): Điểm KPI được tính toán và làm tròn xuống để nhường chỗ cho Tiền mặt.
3. **Bù trừ thông minh (Edge cases):**
   - Nếu khoảng cách `Ln - Lk` quá nhỏ (ví dụ `800.000đ`), không thể ép Tiền mặt lên 1 triệu vì sẽ gây lạm chi. Thuật toán chấp nhận Tiền mặt = 800.000đ và đánh tụt KPI về 50 (0đ tiền KPI).
   - Nếu `Ln - Lk` nhỏ đến mức dưới `300.000đ`, hệ thống sẽ hạ điểm KPI sao cho vừa khít và không phát sinh Tiền mặt.
   - Nếu `Ln - Lk < 0` (Thực lĩnh ngoài cao hơn Lương trong), không phát sinh KPI hay Tiền mặt. Cần dùng **Quick Fix Wizard** để gọt bớt công.
4. **Cảnh báo (Soft Warning):** Hệ thống sẽ đổi màu đỏ và hiện gợi ý nếu `Tiền CK (Lk + Mk)` lớn hơn `Lương trong (Ln)`, nhưng không chặn (block) việc lưu dữ liệu để kế toán linh hoạt xử lý.
5. **Chỉnh sửa trực tiếp:** Cho phép sửa trực tiếp cột `Lương trong (Ln)` ngay tại danh sách để điều chỉnh nhanh các trường hợp đặc biệt.
6. **Làm tròn tiền (Rounding Precision):** Để tránh sai số dấu phẩy động (ví dụ 9.2M thành 9.199M), hệ thống luôn thực hiện `round()` về số nguyên VND trước khi thực hiện chia làm tròn nghìn đồng.

## 3. Hệ Thống Cảnh Báo Bất Thường & Gợi Ý
**Vị trí:** `dl_salary_kpi_month.py` (filter) và `dl_salary_kpi_line.py` (tính toán suggestion).

Dữ liệu sẽ bị đánh dấu là "Bất thường" (🚩) và hiện ở tab riêng nếu:
1. **Thực lĩnh ngoài bị âm (`Lk < 0`)**.
2. **Lương nội bộ lớn hơn 140% Thực lĩnh ngoài (`Ln >= Lk * 1.4`)**.
3. **Thực lĩnh ngoài lớn hơn Lương nội bộ (`Lk > Ln`)** (Trường hợp này vi phạm ràng buộc Tiền CK và bắt buộc phải giảm công).

### Logic Gợi ý xử lý (Anomaly Suggestion):
Dựa trên khoảng cách giữa `Ln` và `Lk`, thuật toán ước tính (quy đổi) khoảng cách này ra số ca làm việc `(N, Đ, 0.5N, 0.5Đ)` bằng cách tính đơn giá giờ thực tế của nhân viên.
- **Lk quá cao (Vượt Ln):** Đề xuất **GIẢM CÔNG** (VD: Giảm 2 lần 0.5N hoặc 1 ngày N).
- **Ln quá cao (Cách Lk >= 1.4 lần):** Đề xuất **THÊM CÔNG** (VD: Thêm 3 ngày N).

## 4. Công cụ Sửa Nhanh (Quick Fix Wizard)
**Vị trí:** `wizard/dl_salary_kpi_quick_fix_wizard.py`

Khi gặp các ca bất thường, kế toán không cần lật lại bảng chấm công chi tiết. Thay vào đó, dùng Wizard với các đặc tính:
- **Giao diện thân thiện:** Cho phép nhập số DƯƠNG (để thêm công) và số ÂM (để bớt công) bằng thẻ `<input type="number">`.
- **Logic Giảm Công (Số âm):** Random tìm các ô đang có công `N`/`Đ` tương ứng để gỡ bỏ. Gỡ OT (`0.5N`) thì không ảnh hưởng đến công chính. Gỡ công chính (`N`) thì bay luôn OT đi kèm.
- **Logic Thêm Công (Số dương):** Chỉ tự động rải công vào các ngày **Thứ 2 đến Thứ 7** (Né hoàn toàn Chủ Nhật). Hệ thống quét tìm các ô đang trống để chèn `N` hoặc `Đ`.
- **Validation an toàn:** Bắt lỗi chặn đứng nếu tổng số ngày công sau khi điều chỉnh có nguy cơ vượt qua ngưỡng **27 ngày công chính/tháng**.
- **Bảo toàn dữ liệu (Protected Days):** Các ngày đã bị đánh dấu Đổi Ca (ĐC) hoặc các ngày lân cận ĐC sẽ được đưa vào "Vùng an toàn" không được phép auto-thêm/xoá để tránh làm vỡ cấu trúc ca làm việc phức tạp.
