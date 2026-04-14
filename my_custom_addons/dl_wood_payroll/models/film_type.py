from odoo import models, fields

class DLFilmType(models.Model):
    _name = 'dl.film.type'
    _description = 'Loại Film'
    _order = 'name'

    name = fields.Char(string='Tên loại Film', required=True)
    code = fields.Char(string='Mã Film')
    thickness = fields.Float(string='Độ dày (mm)')
    note = fields.Text(string='Ghi chú')

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Tên loại Film đã tồn tại!'),
        ('code_unique', 'unique(code)', 'Mã Film đã tồn tại!'),
    ]
