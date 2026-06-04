# -*- coding: utf-8 -*-

def format_vietnamese_address(street=None, street2=None, ward=None, district=None, city=None, state_name=None):
    """
    Chuẩn hóa địa chỉ tiếng Việt:
    - ward (Xã/Phường): Thêm tiền tố "Xã " hoặc "Phường " hoặc "Thị trấn " nếu chưa có.
    - district (Quận/Huyện): Thêm tiền tố "Huyện ", "Quận ", "Thị xã ", "Thành phố " nếu chưa có.
    - city (backward compatibility): Dùng làm ward hoặc district tùy logic cũ.
    - state_name (Tỉnh/Thành phố): Thêm tiền tố "Tỉnh " hoặc "Thành phố " nếu chưa có.
    """
    parts = []
    if street:
        parts.append(street.strip())
    if street2:
        parts.append(street2.strip())
        
    # Xử lý Xã/Phường
    ward_str = ward or city
    if ward_str:
        ward_str = ward_str.strip()
        ward_lower = ward_str.lower()
        ward_prefixes = ['xã', 'phường', 'thị trấn', 'quận', 'huyện', 'thị xã', 'thành phố', 'tp']
        if not any(ward_lower.startswith(p) for p in ward_prefixes):
            ward_str = f"Xã {ward_str}"
        parts.append(ward_str)
        
    # Xử lý Quận/Huyện
    if district and district.strip() and district != city:
        district_str = district.strip()
        district_lower = district_str.lower()
        district_prefixes = ['huyện', 'quận', 'thị xã', 'thành phố', 'tp']
        if not any(district_lower.startswith(p) for p in district_prefixes):
            district_str = f"Huyện {district_str}"
        parts.append(district_str)
        
    # Xử lý Tỉnh/Thành phố
    if state_name:
        state_str = state_name.strip()
        state_lower = state_str.lower()
        state_prefixes = ['tỉnh', 'thành phố', 'tp', 'thủ đô']
        if not any(state_lower.startswith(p) for p in state_prefixes):
            state_str = f"Tỉnh {state_str}"
        parts.append(state_str)
        
    return ", ".join(parts) if parts else ""
