import json

data = [
    ('Công Ty TNHH MTV Xuân Thành Hòa Bình', 'Xuân Thành Hòa Bình', 'Công Ty TNHH MTV', 'Số 59 Đường Cao Lỗ, Khu 11-12, Xã Lạc Thuỷ, Tỉnh Phú Thọ', '5400523349', True),
    ('Công Ty TNHH Sản Xuất Và Gia Công Quang Anh', 'Quang Anh', 'Công Ty TNHH', 'Thôn Dương Lâm, Xã Nhã Nam, Tỉnh Bắc Ninh', '2400909523', True),
    ('Công Ty TNHH SX&TMDVTH Bảo An', 'Bảo An', 'Công Ty TNHH', 'Trại Ổi, Xã Trường Sơn, Tỉnh Bắc Ninh', '2400965077', True),
    ('Công Ty TNHH Nghiêm Chữ', 'Nghiêm Chữ', 'Công Ty TNHH', 'Xóm Lũa, Xã Kha Sơn, Tỉnh Thái Nguyên', '4601653515', True),
    ('Công Ty TNHH Đầu Tư Hoàng Liên Sơn Wood', 'Hoàng Liên Sơn Wood', 'Công Ty TNHH', 'Thôn Cã Trong, Xã Tuấn Sơn, Tỉnh Lạng Sơn', '4900908521', True),
    ('Công Ty TNHH Gỗ Lâm Sản Hưng Thịnh', 'Hưng Thịnh', 'Công Ty TNHH', 'Khu Gò Đa, Xã Hương Cần, Tỉnh Phú Thọ', '2601111967', True),
    ('Hợp Tác Xã Tùng Quân', 'Tùng Quân', 'Hợp Tác Xã', 'Xóm Sơ, Xã Lạc Sơn, Tỉnh Phú Thọ', '5400463410', True),
    ('Công Ty TNHH Sản Xuất Và Dịch Vụ Thương Mại Lâm Thịnh', 'Lâm Thịnh', 'Công Ty TNHH', 'Xóm Tân Tiến, Xã Dân Tiến, Tỉnh Thái Nguyên', '4601660174', True),
    ('Công Ty TNHH Thế Kiệt', 'Thế Kiệt', 'Công Ty TNHH', 'Thôn Minh Tân, Xã Yên Lãng, Tỉnh Phú Thọ', '2500684288', True),
    ('Công Ty TNHH Trường Giang Hòa Bình', 'Trường Giang Hòa Bình', 'Công Ty TNHH', 'Xóm Tân Thành, Xã Nhân Nghĩa, Tỉnh Phú Thọ', '5400543514', True),
    ('Công Ty TNHH Mai Anh HB', 'Mai Anh HB', 'Công Ty TNHH', 'Thôn Đồng Phú, Xã Lạc Thủy, Tỉnh Phú Thọ', '5400511128', True),
    ('Công Ty TNHH Tâm An Phát HT', 'Tâm An Phát HT', 'Công Ty TNHH', 'Bản Đồng Tân, Xã Đồng Kỳ, Tỉnh Bắc Ninh', '2401049246', True),
    ('Công Ty TNHH Chế Biến Lâm Sản Long Phát', 'Long Phát', 'Công Ty TNHH', 'Thôn Lay, Xã Thiện Tân, Tỉnh Lạng Sơn', '4900936751', True),
    ('Công Ty TNHH Sản Xuất Phúc Lâm Thịnh', 'Phúc Lâm Thịnh', 'Công Ty TNHH', 'Xóm Bến Trăm, Xã Bố Hạ, Tỉnh Bắc Ninh', '2401064332', True),
    ('Công Ty TNHH Sản Xuất Và Thương Mại Dịch Vụ Hùng Cường', 'Hùng Cường', 'Công Ty TNHH', 'Thôn Thống Nhất, Xã Tây Yên Tử, Tỉnh Bắc Ninh', '2400989751', True),
    ('Bế Văn Thuận', 'Bế Văn Thuận', 'Cá nhân', 'Thôn Phe, Xã Vân Sơn, Tỉnh Bắc Ninh', '020083001847', False),
    ('Công Ty TNHH S&B Wood', 'S&B Wood', 'Công Ty TNHH', 'Xóm Đồng Yên, Xã Xuân Lộc, Tỉnh Hà Tĩnh', '3002259701', True),
    ('Công Ty TNHH Đại Hải Kim Phát', 'Đại Hải Kim Phát', 'Công Ty TNHH', 'Thôn De, Xã Tiên Lục, Tỉnh Bắc Ninh', '2401052016', True),
    ('Công Ty TNHH Thương Mại Và Sản Xuất Lâm Sản Minh Tú', 'Minh Tú', 'Công Ty TNHH', 'Thôn Luồng, Xã Đèo Gia, Tỉnh Bắc Ninh', '2400976209', True),
    ('Vy Thanh Quý', 'Vy Thanh Quý', 'Cá nhân', 'Thôn Lọ, Xã An Lạc, Tỉnh Bắc Ninh', '024168003457', False),
    ('Công Ty TNHH An Phát THB', 'An Phát THB', 'Công Ty TNHH', 'Xóm Nà Bờ, Xã Hợp Kim, Tỉnh Phú Thọ', '5400542278', True),
    ('Công Ty TNHH Sản Xuất Ly Duy', 'Ly Duy', 'Công Ty TNHH', 'Xóm Bến Trăm, Xã Bố Hạ, Tỉnh Bắc Ninh', '2401068376', True),
    ('Công Ty TNHH Sản Xuất Chế Biến Lâm Sản Tân Tiến', 'Tân Tiến', 'Công Ty TNHH', 'Gia Đình Ông Hồ Bá Tân, Khu Phố Hải Tiến, Xã Như Thanh, Tỉnh Thanh Hóa', '2802927032', True),
    ('Công Ty TNHH Xuất Khẩu Vietwood', 'Vietwood', 'Công Ty TNHH', 'Khu TĐC Công Viên Quảng Trường, Phường Vĩnh Phúc, Tỉnh Phú Thọ', '0110034812', True),
    ('Công Ty TNHH Sản Xuất Quyết Định', 'Quyết Định', 'Công Ty TNHH', 'Xóm Mỹ Hoà, Xã Nam Hòa, Tỉnh Thái Nguyên', '4601665045', True),
    ('Công Ty TNHH Lâm Sản Linh Ngọc', 'Linh Ngọc', 'Công Ty TNHH', 'Thôn 22, Xã Tân Long, Tỉnh Tuyên Quang', '5000916539', True),
    ('Công Ty TNHH Lâm Sản Tiến Đạt LS', 'Tiến Đạt LS', 'Công Ty TNHH', 'Thôn Văn Miêu, Xã Tuấn Sơn, Tỉnh Lạng Sơn', '4900905231', True),
    ('Công Ty TNHH Thương Mại Sản Xuất Và Dịch Vụ Duy Hương', 'Duy Hương', 'Công Ty TNHH', 'Nhà Ông Nguyễn Xuân Duy - Thôn Phú Quế, Xã Như Xuân, Tỉnh Thanh Hóa', '2803192944', True),
    ('Công Ty TNHH Chế Biến Lâm Sản Ngọc Mai', 'Ngọc Mai', 'Công Ty TNHH', 'Khu 10, Xã Đông Thành, Tỉnh Phú Thọ', '2601039710', True),
    ('Công Ty TNHH Dịch Vụ & SX Thương Mại Ngọc Long', 'Ngọc Long', 'Công Ty TNHH', 'Bản Mỏ Trạng, Xã Tam Tiến, Tỉnh Bắc Ninh', '2400968053', True),
    ('Công Ty TNHH Techwood Vina', 'Techwood Vina', 'Công Ty TNHH', 'Số 50, Ngõ 670 Đường Ngô Gia Tự, Phường Việt Hưng, Thành Phố Hà Nội', '0108281243', True),
    ('Công Ty TNHH Phát Triển Dịch Vụ Và Thương Mại XNK Sơn Hà', 'Sơn Hà', 'Công Ty TNHH', 'Thôn Sẩy, Xã Hữu Lũng, Tỉnh Lạng Sơn', '4900891772', True),
    ('Công Ty TNHH Ván Bóc Duy Khánh', 'Duy Khánh', 'Công Ty TNHH', 'Thôn La Thành, Xã Tam Tiến, Tỉnh Bắc Ninh', '2401063240', True),
    ('Công Ty TNHH Sản Xuất Và Thương Mại Gỗ Lê Dũng', 'Lê Dũng', 'Công Ty TNHH', 'Thôn Tiến Thịnh, Xã Tam Tiến, Tỉnh Bắc Ninh', '2401059195', True),
    ('Công Ty Cổ Phần Chế Biến Lâm Sản Khánh An', 'Khánh An', 'Công Ty CP', 'Thôn Lay, Xã Thiện Tân, Tỉnh Lạng Sơn', '4900880925', True),
    ('Công Ty TNHH Sản Xuất Và Thương Mại Heng Xin', 'Heng Xin', 'Công Ty TNHH', 'Thôn Bến Lường, Xã Tuấn Sơn, Tỉnh Lạng Sơn', '4900915864', True),
    ('Công Ty TNHH Dịch Vụ Thương Mại Trọng Tuấn', 'Trọng Tuấn', 'Công Ty TNHH', 'Thôn Bo Chợ, Xã Bố Hạ, Tỉnh Bắc Ninh', '2401063794', True),
    ('Công Ty TNHH SXTM Thành Long', 'Thành Long', 'Công Ty TNHH', 'Thôn Liên Phương, Xã Thiện Tân, Tỉnh Lạng Sơn', '4900938702', True),
    ('Công Ty TNHH SXTM Xuân Hiệu', 'Xuân Hiệu', 'Công Ty TNHH', 'Thôn Lay, Xã Thiện Tân, Tỉnh Lạng Sơn', '4900938759', True),
    ('Công Ty TNHH Sản Xuất Hùng Nga', 'Hùng Nga', 'Công Ty TNHH', 'Thôn Đèo Hanh, Xã Trại Cau, Tỉnh Thái Nguyên', '4601663471', True),
    ('Công Ty TNHH Sản Xuất Long Quyên', 'Long Quyên', 'Công Ty TNHH', 'Xóm Trại Cau, Xã Nam Hòa, Tỉnh Thái Nguyên', '4601663746', True),
    ('Công Ty TNHH Lâm Sản Xây Dựng Vượng Phát', 'Vượng Phát', 'Công Ty TNHH', 'Xóm Cã Ngoài, Xã Tuấn Sơn, Tỉnh Lạng Sơn', '4900885112', True),
    ('Hợp Tác Xã Sản Xuất Chế Biến Lâm Sản Tam Tiến', 'Tam Tiến', 'Hợp Tác Xã', 'Bản Bãi Lát, Xã Tam Tiến, Tỉnh Bắc Ninh', '2401005778', True),
    ('Công Ty TNHH Sản Xuất & Thương Mại Minh Hiếu NH', 'Minh Hiếu NH', 'Công Ty TNHH', 'Xóm Đoàn Kết, Xã Nam Hòa, Tỉnh Thái Nguyên', '4601653441', True),
    ('Công Ty TNHH Phi Long Wood', 'Phi Long Wood', 'Công Ty TNHH', 'Bản Quỳnh Lâu, Xã Tam Tiến, Tỉnh Bắc Ninh', '2401061525', True),
    ('Công Ty TNHH Lâm Sản Quang Dương', 'Quang Dương', 'Công Ty TNHH', 'Xóm Bãi Bông, Xã Trại Cau, Tỉnh Thái Nguyên', '4601660054', True),
    ('Công Ty TNHH Thanh Liêm TN', 'Thanh Liêm TN', 'Công Ty TNHH', 'TDP Cầu Lưu, Xã Trại Cau, Tỉnh Thái Nguyên', '4601637545', True),
    ('Công Ty TNHH SX Và TM TTN Woods', 'TTN Woods', 'Công Ty TNHH', 'Thôn 6, Xã Trại Cau, Tỉnh Thái Nguyên', '4601665327', True),
    ('Công Ty TNHH Sản Xuất Chiến Hà', 'Chiến Hà', 'Công Ty TNHH', 'Thôn Cao Phong, Xã Trại Cau, Tỉnh Thái Nguyên', '4601665888', True),
    ('Công Ty TNHH Xuất Nhập Khẩu Tiến Thịnh Wood', 'Tiến Thịnh Wood', 'Công Ty TNHH', 'Thôn Quàn, Xã Thượng Hồng, Thành Phố Hải Phòng', '2400964651', True),
    ('Công Ty TNHH Dịch Vụ Tổng Hợp Linh My Chi Thắng', 'Linh My Chi Thắng', 'Công Ty TNHH', 'Thôn Hòa Bình, Xã Bố Hạ, Tỉnh Bắc Ninh', '2400901612', True),
    ('Công Ty TNHH Lê Anh Thư Phú Thọ', 'Lê Anh Thư Phú Thọ', 'Công Ty TNHH', 'Khu 5 Đại Phạm, Xã Đan Thượng, Tỉnh Phú Thọ', '2601150010', True),
    ('Công Ty CP Xây Lắp 188', '188', 'Công Ty CP', 'Lô 42, 43 - Phân Khu N18 - Khu Đô Thị Mới Phía Tây, Xã Lạng Giang, Tỉnh Bắc Ninh', '2401008754', True),
    ('Công Ty TNHH Ngô Hoàng Phú', 'Ngô Hoàng Phú', 'Công Ty TNHH', 'Bản Quỳnh Lâu, Xã Tam Tiến, Tỉnh Bắc Ninh', '2401068834', True),
    ('Công Ty TNHH Sản Xuất Và XNK Dũng Linh', 'Dũng Linh', 'Công Ty TNHH', 'TDP Hoà Bình, Xã Bố Hạ, Tỉnh Bắc Ninh', '2401008553', True),
    ('Công Ty TNHH Sản Xuất Và Thương Mại Hải Hồng', 'Hải Hồng', 'Công Ty TNHH', 'Bản Nam Cầu, Xã Xuân Lương, Tỉnh Bắc Ninh', '2401071555', True),
    ('Công Ty TNHH Kinh Doanh Và Sản Xuất Tú Anh', 'Tú Anh', 'Công Ty TNHH', 'Thôn Khánh Xuân, Xã Hùng Đức, Tỉnh Tuyên Quang', '5000899114', True),
    ('Công Ty TNHH Đại Tùng Lâm VN', 'Đại Tùng Lâm VN', 'Công Ty TNHH', 'Thôn Liên Phương, Xã Thiện Tân, Tỉnh Lạng Sơn', '4900937681', True),
    ('Công Ty Cổ Phần Sản Xuất Và Thương Mại Quang Minh 79', 'Quang Minh 79', 'Công Ty CP', 'Khu Tân Mỹ 2, Xã Hữu Lũng, Tỉnh Lạng Sơn', '4900922692', True),
    ('Công Ty TNHH Thương Mại Minh Châu TQ', 'Minh Châu TQ', 'Công Ty TNHH', 'Tổ Dân Phố Núi Cẩy, Phường An Tường, Tỉnh Tuyên Quang', '5000915292', True),
    ('Công Ty TNHH Ngọc Minh Wood', 'Ngọc Minh Wood', 'Công Ty TNHH', 'Thôn Phổng, Xã Vân Nham, Tỉnh Lạng Sơn', '4900916843', True),
    ('Công Ty TNHH Quốc Anh YB', 'Quốc Anh YB', 'Công Ty TNHH', 'Tổ Dân Phố 1, Xã Thác Bà, Tỉnh Lào Cai', '5200944967', True),
    ('Công Ty TNHH Lâm Sản Thanh Phong', 'Thanh Phong', 'Công Ty TNHH', 'Thôn Đồng Cướm, Xã Trung Sơn, Tỉnh Tuyên Quang', '5000916017', True),
    ('Công Ty TNHH Phát Triển Dịch Vụ Và Thương Mại Linh Anh', 'Linh Anh', 'Công Ty TNHH', 'Thôn Cã Trong, Xã Tuấn Sơn, Tỉnh Lạng Sơn', '4900891684', True),
    ('Công Ty TNHH Sản Xuất Ván Bóc Nghệ An', 'Nghệ An', 'Công Ty TNHH', 'Xóm Đức Thịnh, Xã Tân Phú, Tỉnh Nghệ An', '2902159507', True),
    ('Doanh Nghiệp Tư Nhân Chế Biến Lâm Sản Đồng Kha', 'Đồng Kha', 'DNTN', 'Thôn Giàng, Xã Linh Sơn, Tỉnh Thanh Hóa', '2802139641', True),
    ('Công Ty TNHH Sản Xuất Đại Châu', 'Đại Châu', 'Công Ty TNHH', 'Xóm Mìn, Xã Dân Tiến, Tỉnh Thái Nguyên', '4601663753', True),
    ('Công Ty TNHH Tuấn Linh Wood', 'Tuấn Linh Wood', 'Công Ty TNHH', 'Thôn An Phú, Xã Tân An, Tỉnh Tuyên Quang', '5000911481', True),
    ('Công Ty TNHH Dịch Vụ Và Thương Mại Tuấn Nhật', 'Tuấn Nhật', 'Công Ty TNHH', 'Thôn Lập Thành, Xã Thái Hòa, Tỉnh Tuyên Quang', '5000898181', True),
]

json_data = []
for row in data:
    if len(row) == 6:
        name, short_name, loai_dn, dia_chi, vat, is_company = row
    else:
        continue
    
    json_data.append({
        "name": name,
        "vat": vat,
        "is_company": is_company,
        "street": dia_chi,
        "x_company_type_label": loai_dn
    })

with open('my_custom_addons/dl_wood_traceability/data/peeling_suppliers.json', 'w', encoding='utf-8') as f:
    json.dump(json_data, f, ensure_ascii=False, indent=4)
