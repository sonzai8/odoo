# -*- coding: utf-8 -*-

def calculate_allowances(rec):
    """Tính toán các khoản hỗ trợ & phụ cấp pro-rated theo 26 ngày"""
    total_work_days = rec.total_n + rec.total_d
    
    meal_allowance = (rec.month_id.dl_meal_allowance * total_work_days) / 26.0 if total_work_days > 0 else 0
    
    is_female = rec.employee_id.sex == 'female'
    women_allowance = (rec.month_id.dl_women_allowance * total_work_days) / 26.0 if (is_female and total_work_days > 0) else 0
    
    return meal_allowance, women_allowance

def calculate_annual_bonuses(rec):
    """Tính toán các khoản thưởng cố định trong năm"""
    b0803, b3004, b0209, btet, bother = 0.0, 0.0, 0.0, 0.0, 0.0
    is_female = rec.employee_id.sex == 'female'
    
    for bl in rec.month_id.bonus_line_ids:
        # Kiểm tra giới tính áp dụng
        if bl.gender == 'male' and not rec.employee_id.sex == 'male': continue
        if bl.gender == 'female' and not is_female: continue
        
        name = bl.name or ""
        if '08/03' in name: b0803 += bl.amount
        elif '30/04' in name: b3004 += bl.amount
        elif '02/09' in name: b0209 += bl.amount
        elif 'Tết' in name and 'Dương Lịch' in name: btet += bl.amount
        else: bother += bl.amount
        
    return b0803, b3004, b0209, btet, bother

def calculate_revenue_productivity_bonuses(rec):
    """Tính toán thưởng doanh thu & năng suất theo QĐ 3108"""
    total_work_days = rec.total_n + rec.total_d
    revenue = rec.month_id.dl_revenue or 0

    rev_bonus_base = 0
    if revenue > 70_000_000_000: rev_bonus_base = 3_500_000
    elif revenue > 50_000_000_000: rev_bonus_base = 3_000_000
    elif revenue > 30_000_000_000: rev_bonus_base = 2_300_000
    elif revenue > 20_000_000_000: rev_bonus_base = 2_000_000
    
    revenue_bonus = (rev_bonus_base * total_work_days) / 26.0
    productivity_bonus = 0.0 # Hiện tại chưa dùng theo yêu cầu mới nhất
    
    print("Revenue Bonus: ", revenue_bonus)
    print("Productivity Bonus: ", productivity_bonus)

    return revenue_bonus, productivity_bonus, rev_bonus_base

def calculate_detailed_wages(rec):
    """Tính toán lương chi tiết dựa trên mã công và giờ làm việc"""
    hourly_rate = rec.dl_tax_base_salary / 208.0 if rec.dl_tax_base_salary else 0
    
    wages = {
        'wage_day': 0.0,
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
        
        # Ca ngày thường & Nghỉ hưởng lương (P, PL)
        if att and att.code in ['N', 'N/1', 'N/2', 'P', 'PL']:
            # P và PL tính như 1 ngày công (8 giờ)
            hours = 8.0 if att.code in ['N', 'P', 'PL'] else 4.0
            wages['wage_day'] += hours * hourly_rate
        
        # Ca đêm thường
        if att and att.code in ['Đ', 'Đ/1', 'Đ/2']:
            hours = 8.0 if att.code == 'Đ' else 4.0
            wages['wage_night_130'] += hours * hourly_rate * 1.3
        
        # Làm thêm giờ
        if ot_att:
            hours = ot_att.weight * 10 
            code = ot_att.code or ""
            
            if ot_att.ot_type == 'day':
                if code == '0.5N': wages['wage_day_150'] += hours * hourly_rate * 1.5
                elif code in ['CNN', 'CNN/2']: wages['wage_day_sun_200'] += hours * hourly_rate * 2.0
                elif code == 'LN': wages['wage_day_holiday_300'] += hours * hourly_rate * 3.0
            
            elif ot_att.ot_type == 'night':
                if code == '0.5Đ':
                    if att: # Có làm ca ngày
                        wages['wage_night_210'] += hours * hourly_rate * 2.1
                    else: # Không làm ca ngày
                        wages['wage_night_200'] += hours * hourly_rate * 2.0
                elif code in ['CNĐ', 'CNĐ/2']: wages['wage_night_sun_270'] += hours * hourly_rate * 2.7
                elif code == 'LĐ': wages['wage_night_holiday_390'] += hours * hourly_rate * 3.9
                
    return wages
