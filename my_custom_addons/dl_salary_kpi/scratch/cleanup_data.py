# -*- coding: utf-8 -*-
import os
import sys

# Giả lập môi trường Odoo
# (Đường dẫn có thể cần điều chỉnh tùy theo cấu trúc thư mục)
# Ở đây tôi sẽ sử dụng shell command nếu có thể, hoặc tạo 1 script chạy bằng odoo-bin shell

def cleanup_duplicates():
    # Tìm tất cả các bản ghi CNN/2
    # Giữ lại bản ghi có ID nhỏ nhất (thường là bản ghi gốc từ XML)
    # Xóa các bản ghi khác
    pass

if __name__ == "__main__":
    print("Cleanup script ready")
