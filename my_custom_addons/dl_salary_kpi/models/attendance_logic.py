# -*- coding: utf-8 -*-
from datetime import date
from calendar import monthrange

def calculate_attendance_totals(rec):
    """
    Tính tổng các loại công từ ma trận chấm công 1-31.
    Trả về một dict chứa các giá trị tổng hợp.
    """
    n, d, p, pl, kp, o, dc, co = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    ot_n, ot_d = 0.0, 0.0
    ot_n_normal, ot_d_normal, ot_n_sun, ot_d_sun, ot_n_holiday, ot_d_holiday = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    ot_d_200 = 0.0 # Tăng ca đêm không làm ca ngày
    
    for i in range(1, 32):
        # 1. Xử lý công thường
        att = getattr(rec, f'day_{i:02d}')
        if att:
            code = att.code
            if code == 'N': n += 1.0
            elif code in ['N/2']: n += 0.5
            elif code == 'Đ': d += 1.0
            elif code in ['Đ/2']: d += 0.5
            elif code == 'P': p += 1.0
            elif code == 'PL': pl += 1.0
            elif code == 'KP': kp += 1.0
            elif code == 'Ô': o += 1.0
            elif code == 'ĐC': dc += 1.0
            elif code == 'CÔ': co += 1.0
        
        # 2. Xử lý làm thêm giờ (OT)
        ot_att = getattr(rec, f'ot_day_{i:02d}')
        if ot_att:
            code = ot_att.code or ""
            hours = ot_att.weight * 10
            
            if ot_att.ot_type == 'day':
                ot_n += hours
                if code == '0.5N': ot_n_normal += hours
                elif code in ['CNN', 'CNN/2']: ot_n_sun += hours
                elif code == 'LN': ot_n_holiday += hours
            elif ot_att.ot_type == 'night':
                ot_d += hours
                if code == '0.5Đ':
                    if not att: # Không làm ca ngày
                        ot_d_200 += hours
                    else:
                        ot_d_normal += hours
                elif code in ['CNĐ', 'CNĐ/2', 'CND/2']: ot_d_sun += hours
                elif code == 'LĐ': ot_d_holiday += hours

    return {
        'total_n': n, 'total_d': d, 'total_p': p, 'total_pl': pl,
        'total_kp': kp, 'total_o': o, 'total_dc': dc, 'total_co': co,
        'ot_n': ot_n, 'ot_d': ot_d, 'ot_all': ot_n + ot_d,
        'ot_n_normal': ot_n_normal, 'ot_d_normal': ot_d_normal,
        'ot_n_sun': ot_n_sun, 'ot_d_sun': ot_d_sun,
        'ot_n_holiday': ot_n_holiday, 'ot_d_holiday': ot_d_holiday,
        'ot_d_200': ot_d_200
    }

def get_attendance_summary_html(rec):
    """
    Tạo chuỗi HTML hiển thị tóm tắt mã công trong tháng cho nhân viên.
    """
    counts = {}
    ot_counts = {}
    for i in range(1, 32):
        att = getattr(rec, f'day_{i:02d}')
        if att:
            counts[att.code] = counts.get(att.code, 0) + 1
            
        ot_att = getattr(rec, f'ot_day_{i:02d}')
        if ot_att:
            ot_counts[ot_att.code] = ot_counts.get(ot_att.code, 0) + 1
            
    html = "<div class='row'><div class='col-6'><strong>Công thường:</strong><ul>"
    if not counts:
        html += "<li>(Không có)</li>"
    else:
        for code, count in sorted(counts.items()):
            html += f"<li>{code}: {count} ngày</li>"
    html += "</ul></div><div class='col-6'><strong>Tăng ca:</strong><ul>"
    if not ot_counts:
        html += "<li>(Không có)</li>"
    else:
        for code, count in sorted(ot_counts.items()):
            html += f"<li>{code}: {count} ngày</li>"
    html += "</ul></div></div>"
    return html

def get_day_metadata(date_month):
    """
    Tính toán thông tin metadata cho từng ngày trong tháng (Chủ nhật, Tuần, Thứ).
    """
    if not date_month:
        return {}
        
    year, month = date_month.year, date_month.month
    last_day = monthrange(year, month)[1]
    
    metadata = {}
    current_week = 1
    for i in range(1, 32):
        if i <= last_day:
            d = date(year, month, i)
            if d.weekday() == 0 and i > 1:
                current_week += 1
            
            metadata[i] = {
                'is_sunday': (d.weekday() == 6),
                'week': current_week,
                'row': d.weekday() + 1
            }
        else:
            metadata[i] = {'is_sunday': False, 'week': 0, 'row': 0}
    return metadata

def check_departure_date_violation(rec):
    """
    Kiểm tra xem nhân viên có phát sinh công sau ngày nghỉ việc hay không.
    Trả về dict các trường cần xoá (False).
    """
    dep_date = rec.employee_id.dl_departure_date
    month_date = rec.month_id.date_month
    if not dep_date or not month_date:
        return {}
        
    year, month = month_date.year, month_date.month
    vals_to_clear = {}
    for i in range(1, 32):
        try:
            d = date(year, month, i)
            if d > dep_date:
                if getattr(rec, f'day_{i:02d}'):
                    vals_to_clear[f'day_{i:02d}'] = False
                if getattr(rec, f'ot_day_{i:02d}'):
                    vals_to_clear[f'ot_day_{i:02d}'] = False
        except ValueError:
            continue
    return vals_to_clear

def check_shift_change_violation(rec):
    """
    Kiểm tra quy tắc đổi ca: Đêm (Đ) sang Ngày (N) phải có Đổi ca (ĐC).
    Trả về (is_error, day_index)
    """
    for i in range(1, 31):
        current_day = getattr(rec, f'day_{i:02d}')
        next_day = getattr(rec, f'day_{i+1:02d}')
        if current_day and next_day:
            if current_day.code == 'Đ' and next_day.code == 'N':
                return True, i
    return False, 0

def check_sunday_attendance_violation(rec):
    """
    Kiểm tra nếu có chấm công thường vào ngày Chủ Nhật.
    Trả về day_index nếu vi phạm, ngược lại trả về 0.
    """
    for i in range(1, 32):
        day_field = f'day_{i:02d}'
        is_sun_field = f'day_{i:02d}_is_sunday'
        if getattr(rec, day_field) and getattr(rec, is_sun_field):
            return i
    return 0
