# -*- coding: utf-8 -*-

def calculate_allowances(rec):
    """Tính toán các khoản hỗ trợ & phụ cấp pro-rated theo 26 ngày"""
    total_work_days = rec.total_n + rec.total_d
    
    meal_allowance = (rec.month_id.dl_meal_allowance * total_work_days) / 26.0 if total_work_days > 0 else 0
    
    is_female = rec.employee_id.sex == 'female'
    women_allowance = (rec.month_id.dl_women_allowance * total_work_days) / 26.0 if (is_female and total_work_days > 0) else 0
    
    return meal_allowance, women_allowance

def calculate_annual_bonuses(rec):
    """Tính toán các khoản thưởng cố định trong năm (Thực tế và Tiềm năng)"""
    # Actual (Thực nhận dựa trên công)
    act = {'b0803': 0.0, 'b3004': 0.0, 'b0209': 0.0, 'btet': 0.0, 'bother': 0.0}
    # Potential (Mức thưởng tối đa nếu đi làm)
    pot = {'b0803': 0.0, 'b3004': 0.0, 'b0209': 0.0, 'btet': 0.0, 'bother': 0.0}
    
    is_female = rec.employee_id.sex == 'female'
    
    for bl in rec.month_id.bonus_line_ids:
        # 1. Kiểm tra giới tính
        if bl.gender == 'male' and not rec.employee_id.sex == 'male': continue
        if bl.gender == 'female' and not is_female: continue
        
        name = bl.name or ""
        # Ghi nhận vào mức Tiềm năng (Luôn cộng)
        if '08/03' in name: pot['b0803'] += bl.amount
        elif '30/04' in name: pot['b3004'] += bl.amount
        elif '02/09' in name: pot['b0209'] += bl.amount
        elif 'Tết' in name and 'Dương Lịch' in name: pot['btet'] += bl.amount
        else: pot['bother'] += bl.amount

        # 2. KIỂM TRA ĐIỀU KIỆN NGHỈ VIỆC
        # Chỉ cần nhân viên không nghỉ việc trước hoặc đúng ngày thưởng là được nhận
        is_eligible = True
        if bl.date and rec.employee_id.departure_date:
            if rec.employee_id.departure_date <= bl.date:
                is_eligible = False
        
        if is_eligible:
            if '08/03' in name: act['b0803'] += bl.amount
            elif '30/04' in name: act['b3004'] += bl.amount
            elif '02/09' in name: act['b0209'] += bl.amount
            elif 'Tết' in name and 'Dương Lịch' in name: act['btet'] += bl.amount
            else: act['bother'] += bl.amount
        
    return act, pot

POSITION_GROUP_MAP = {
    # QLCC
    'CV': 'QLCC', 'KTT': 'QLCC', 'QL': 'QLCC', 'QĐ': 'QLCC',
    'TL': 'QLCC', 'PGĐ': 'QLCC', 'GĐ': 'QLCC',
    # NVGT
    'NV': 'NVGT', 'KT': 'NVGT', 'TK': 'NVGT',
    # NVSX
    'CN': 'NVSX', 'LX': 'NVSX',
}

def calculate_revenue_productivity_bonuses(rec):
    """Tính toán thưởng doanh thu & năng suất theo QĐ mới nhất"""
    total_work_days = rec.total_n + rec.total_d
    revenue = rec.month_id.dl_revenue or 0
    
    position = rec.employee_id.dl_tax_position or ''
    group = POSITION_GROUP_MAP.get(position, '')

    rev_bonus_base = 0
    prod_bonus_base = 0
    
    # 1. Tính mức Thưởng Doanh Thu (Áp dụng chung cho TẤT CẢ)
    if revenue > 70_000_000_000:
        rev_bonus_base = 3_500_000
    elif revenue > 50_000_000_000:
        rev_bonus_base = 3_000_000
    elif revenue > 30_000_000_000:
        rev_bonus_base = 2_300_000
    elif revenue > 20_000_000_000:
        rev_bonus_base = 2_000_000
        
    revenue_bonus = (rev_bonus_base * total_work_days) / 26.0

    # 2. Tính mức Thưởng Năng Suất (Theo Nhóm chức vụ, áp dụng cho TẤT CẢ)
    if group == 'QLCC':
        prod_bonus_base = 2_000_000
    elif group == 'NVGT':
        prod_bonus_base = 1_500_000
    elif group == 'NVSX':
        prod_bonus_base = 1_000_000
        
    productivity_bonus = (prod_bonus_base * total_work_days) / 26.0

    return revenue_bonus, productivity_bonus, rev_bonus_base, prod_bonus_base

def calculate_detailed_wages(rec):
    """Tính toán lương chi tiết dựa trên mã công và giờ làm việc"""
    hourly_rate = rec.dl_tax_base_salary / 208.0 if rec.dl_tax_base_salary else 0
    
    wages = {
        'wage_day': 0.0,
        'wage_leave': 0.0,
        'wage_bonus_p': 0.0,
        'wage_day_150': 0.0,
        'wage_night_130': 0.0,
        'wage_night_200': 0.0,
        'wage_night_210': 0.0,
        'wage_night_sun_270': 0.0,
        'wage_day_sun_200': 0.0,
        'wage_day_holiday_300': 0.0,
        'wage_night_holiday_390': 0.0,
    }
    
    for i in range(1, 32):
        att = getattr(rec, f'day_{i:02d}')
        ot_att = getattr(rec, f'ot_day_{i:02d}')
        
        # Ca ngày thường (N, N/2)
        if att and att.code in ['N', 'N/2']:
            hours = 8.0 if att.code == 'N' else 4.0
            wages['wage_day'] += hours * hourly_rate
            
        # Nghỉ hưởng lương (P, PL) - Được miễn thuế 100%
        elif att and att.code in ['P', 'PL']:
            wages['wage_leave'] += 8.0 * hourly_rate
        
        # Ca đêm thường (Tách 31.25% vào lương ngày, 68.75% vào lương đêm 130%)
        if att and att.code in ['Đ', 'Đ/2']:
            hours = 8.0 if att.code == 'Đ' else 4.0
            wages['wage_day'] += hours * 0.3125 * hourly_rate
            wages['wage_night_130'] += hours * 0.6875 * hourly_rate * 1.3
        
        # Làm thêm giờ
        if ot_att:
            hours = ot_att.weight * 8 
            code = ot_att.code or ""
            
            if ot_att.ot_type == 'day':
                if code == '0.5N': wages['wage_day_150'] += hours * hourly_rate * 1.5
                elif code in ['CNN', 'CNN/2']: wages['wage_day_sun_200'] += hours * hourly_rate * 2.0
                elif code == 'LN': wages['wage_day_holiday_300'] += hours * hourly_rate * 3.0
            
            elif ot_att.ot_type == 'night':
                if code == '0.5Đ':
                    # Tất cả làm thêm đêm 0.5Đ hiện tại thống nhất tính 200%
                    wages['wage_night_200'] += hours * hourly_rate * 2.0
                    wages['wage_night_210'] = 0.0
                elif code in ['CNĐ', 'CNĐ/2']: wages['wage_night_sun_270'] += hours * hourly_rate * 2.7
                elif code == 'LĐ': wages['wage_night_holiday_390'] += hours * hourly_rate * 3.9
                
    # Thưởng chuyên cần: Được tính riêng (Cộng vào thực lĩnh nhưng miễn thuế 100%)
    if getattr(rec, 'bonus_p_day', 0.0):
        wages['wage_bonus_p'] += rec.bonus_p_day * 8.0 * hourly_rate
        
    return wages

def calculate_deductions(rec, total_actual_income, meal_allowance):
    """
    Tính toán các khoản khấu trừ bảo hiểm & thuế TNCN (4 bước).
    
    Bước 1: Tính Thu nhập chịu thuế (TNCT) = Tổng thu nhập - Miễn thuế tiền ăn.
    Bước 2: Tính Tổng các khoản giảm trừ (BH + Bản thân + NPT).
    Bước 3: Tính Thu nhập tính thuế (TNTT) = TNCT - Tổng giảm trừ.
    Bước 4: Tính Thuế TNCN theo biểu thuế lũy tiến 5 bậc.
    """
    company = rec.env.company
    personal_deduction = company.dl_pit_personal_deduction or 15500000.0
    dependent_deduction = company.dl_pit_dependent_deduction or 6200000.0
    
    # 0. Bảo hiểm bắt buộc (Tính trên lương cơ bản thuế)
    # KIỂM TRA DANH SÁCH CẮT BẢO HIỂM
    insurance_stopped = rec.employee_id.id in rec.month_id.insurance_stop_ids.mapped('employee_id').ids
    
    base_insurance = rec.dl_tax_base_salary or 0.0
    
    # Mức bảo hiểm dùng để tính GIẢM TRỪ THUẾ (Giữ nguyên logic cũ)
    bhxh_for_tax = round(base_insurance * 0.08, 0)
    bhyt_for_tax = round(base_insurance * 0.015, 0)
    bhtn_for_tax = round(base_insurance * 0.01, 0)
    insurance_for_tax = bhxh_for_tax + bhyt_for_tax + bhtn_for_tax

    # Mức bảo hiểm THỰC TRỪ vào lương (Bằng 0 nếu bị cắt)
    if insurance_stopped:
        bhxh = 0.0
        bhyt = 0.0
        bhtn = 0.0
    else:
        bhxh = bhxh_for_tax
        bhyt = bhyt_for_tax
        bhtn = bhtn_for_tax
        
    total_insurance = bhxh + bhyt + bhtn

    # 1. Thu nhập chịu thuế (TNCT)
    # Ghi chú: total_actual_income đã bao gồm lương ngày thưởng chuyên cần.
    # Theo yêu cầu: Luôn miễn thuế cho toàn bộ tiền trợ cấp ăn ca thực tế.
    taxable_income = total_actual_income - meal_allowance
    
    # 2. Tổng các khoản giảm trừ
    num_dependents = len(rec.employee_id.dependent_ids)
    # SỬ DỤNG insurance_for_tax ĐỂ GIỮ NGUYÊN LOGIC THUẾ
    total_deductions = insurance_for_tax + personal_deduction + (num_dependents * dependent_deduction)
    
    # 3. Thu nhập tính thuế (TNTT)
    assessable_income = max(0.0, taxable_income - total_deductions)
    
    # 4. Thuế TNCN (Biểu thuế lũy tiến 5 bậc)
    tncn = 0.0
    tntt = assessable_income
    if tntt > 0:
        if tntt <= 10000000:
            tncn = tntt * 0.05
        elif tntt <= 30000000:
            tncn = (tntt * 0.10) - 500000
        elif tntt <= 60000000:
            tncn = (tntt * 0.20) - 3500000
        elif tntt <= 100000000:
            tncn = (tntt * 0.30) - 9500000
        else:
            tncn = (tntt * 0.35) - 14500000
    
    tncn = round(tncn, 0)
    total_deduction = total_insurance + tncn
    
    return {
        'bhxh': bhxh,
        'bhyt': bhyt,
        'bhtn': bhtn,
        'tncn': tncn,
        'total_insurance': total_insurance,
        'total_deduction': total_deduction,
        'taxable_income': taxable_income,
        'num_dependents': num_dependents,
        'total_pit_deductions': total_deductions,
        'assessable_income': assessable_income,
    }
