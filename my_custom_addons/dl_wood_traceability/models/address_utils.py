# -*- coding: utf-8 -*-

def format_vietnamese_address(street=None, street2=None, city=None, state_name=None):
    """
    Chuẩn hóa địa chỉ tiếng Việt:
    - city (Xã/Phường): Thêm tiền tố "Xã " hoặc "Phường " hoặc "Thị trấn " nếu chưa có.
    - state_name (Tỉnh/Thành phố): Thêm tiền tố "Tỉnh " hoặc "Thành phố " nếu chưa có.
    """
    parts = []
    if street:
        parts.append(street.strip())
    if street2:
        parts.append(street2.strip())
        
    if city:
        city_str = city.strip()
        city_lower = city_str.lower()
        prefixes = ['xã', 'phường', 'thị trấn', 'quận', 'huyện', 'thị xã', 'thành phố', 'tp']
        if not any(city_lower.startswith(p) for p in prefixes):
            city_str = f"Xã {city_str}"
        parts.append(city_str)
        
    if state_name:
        state_str = state_name.strip()
        state_lower = state_str.lower()
        prefixes = ['tỉnh', 'thành phố', 'tp', 'thủ đô']
        if not any(state_lower.startswith(p) for p in prefixes):
            state_str = f"Tỉnh {state_str}"
        parts.append(state_str)
        
    return ", ".join(parts) if parts else ""
