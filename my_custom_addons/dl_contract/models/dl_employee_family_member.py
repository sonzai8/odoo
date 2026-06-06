# -*- coding: utf-8 -*-
from odoo import models, fields

class DlEmployeeFamilyMember(models.Model):
    _name = 'dl.employee.family.member'
    _description = 'Thành viên Gia đình Nhân viên'
    _order = 'dl_relation, id'

    employee_id = fields.Many2one('hr.employee', string='Nhân viên', ondelete='cascade', required=True, index=True)
    
    dl_name = fields.Char(string='Họ tên', required=True)
    dl_birthday = fields.Date(string='Ngày sinh')
    dl_gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác')
    ], string='Giới tính', default='male')
    dl_ethnic_name = fields.Selection([
        ('1', 'Kinh'),
        ('2', 'Tày'),
        ('3', 'Thái'),
        ('4', 'Hoa'),
        ('5', 'Khơ-me'),
        ('6', 'Mường'),
        ('7', 'Nùng'),
        ('8', 'Hmông'),
        ('9', 'Dao'),
        ('10', 'Gia-rai'),
        ('11', 'Ngái'),
        ('12', 'Ê-đê'),
        ('13', 'Ba-na'),
        ('14', 'Xơ-đăng'),
        ('15', 'Sán Chay'),
        ('16', 'Cơ-ho'),
        ('17', 'Chăm'),
        ('18', 'Sán Dìu'),
        ('19', 'Hrê'),
        ('20', 'Mnông'),
        ('21', 'Ra-glai'),
        ('22', 'Xtiêng'),
        ('23', 'Bru-Vân Kiều'),
        ('24', 'Thổ'),
        ('25', 'Giáy'),
        ('26', 'Cơ-tu'),
        ('27', 'Gié-Triêng'),
        ('28', 'Mạ'),
        ('29', 'Khơ-mú'),
        ('30', 'Co'),
        ('31', 'Ta-ôi'),
        ('32', 'Chơ-ro'),
        ('33', 'Kháng'),
        ('34', 'Xinh-mun'),
        ('35', 'Hà Nhì'),
        ('36', 'Chu-ru'),
        ('37', 'Lào'),
        ('38', 'La Chi'),
        ('39', 'La Ha'),
        ('40', 'Phù Lá'),
        ('41', 'La Hủ'),
        ('42', 'Lự'),
        ('43', 'Lô Lô'),
        ('44', 'Chứt'),
        ('45', 'Mảng'),
        ('46', 'Pà Thẻn'),
        ('47', 'Cơ Lao'),
        ('48', 'Cống'),
        ('49', 'Bố Y'),
        ('50', 'Si La'),
        ('51', 'Pu Péo'),
        ('52', 'Brâu'),
        ('53', 'Ơ Đu'),
        ('54', 'Rơ-măm'),
        ('55', 'Ca dong'),
        ('99', 'Người nước ngoài')
    ], string='Dân tộc', default='1')
    dl_cccd = fields.Char(string='Số CCCD')
    dl_birth_province = fields.Char(string='Tỉnh khai sinh')
    dl_birth_ward = fields.Char(string='Phường khai sinh')
    dl_birth_address = fields.Char(string='Địa chỉ khai sinh')
    dl_relation = fields.Selection([
        ('00', 'Chủ hộ'),
        ('01', 'Vợ'),
        ('02', 'Chồng'),
        ('03', 'Bố'),
        ('04', 'Mẹ'),
        ('05', 'Em'),
        ('06', 'Anh'),
        ('07', 'Chị'),
        ('08', 'Con'),
        ('09', 'Cháu'),
        ('10', 'Ông'),
        ('11', 'Bà'),
        ('12', 'Cô'),
        ('13', 'Dì'),
        ('14', 'Chú'),
        ('15', 'Thím'),
        ('16', 'Bác'),
        ('17', 'Cậu'),
        ('18', 'Mợ'),
        ('19', 'Con dâu'),
        ('20', 'Con rể'),
        ('21', 'Chắt'),
        ('99', 'Khác'),
    ], string='Mối quan hệ với chủ hộ', required=True, default='99')
