# -*- coding: utf-8 -*-
from odoo import models, fields

class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'dl.wood.log.mixin']

    dl_contract_ids = fields.One2many(
        'dl.wood.contract.template', 
        'partner_id', 
        string='Danh sách hợp đồng mẫu'
    )
