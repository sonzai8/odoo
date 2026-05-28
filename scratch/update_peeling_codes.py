import logging

_logger = logging.getLogger(__name__)

def update_peeling_codes(env):
    try:
        peeling_types = env['dl.wood.peeling.type'].sudo().search([])
        for ptype in peeling_types:
            lower_name = ptype.name.lower()
            code = ''
            if 'keo' in lower_name: code = 'K'
            elif 'bạch đàn' in lower_name: code = 'BD'
            elif 'thông' in lower_name: code = 'T'
            elif 'cao su' in lower_name: code = 'CS'
            
            if code and ptype.code != code:
                ptype.code = code
                print(f"Cập nhật mã cho {ptype.name} thành {code}")
        
        env.cr.commit()
        print("Hoàn tất cập nhật mã loại ván bóc!")
        
    except Exception as e:
        env.cr.rollback()
        print(f"Có lỗi xảy ra: {str(e)}")

update_peeling_codes(env)
