# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class DebugMenu(models.Model):
    _name = 'dl.debug.menu'
    _description = 'Debug Tool for Menus'

    def check_sorting_module(self):
        module = self.env['ir.module.module'].search([('name', '=', 'dl_wood_sorting')])
        if not module:
            return "Module dl_wood_sorting NOT FOUND in addons."
        
        status = module.state
        if status != 'installed':
            module.button_immediate_install()
            return f"Module dl_wood_sorting was in state '{status}', attempted to INSTALL."
        
        return f"Module dl_wood_sorting is INSTALLED. Checking menus..."

    def check_menus(self):
        menus = self.env['ir.ui.menu'].search([('name', 'ilike', 'Nhặt Ván')])
        if not menus:
            return "No menu found with name like 'Nhặt Ván'."
        
        res = []
        for m in menus:
            groups = [g.name for g in m.groups_id]
            res.append(f"Menu: {m.complete_name} | ID: {m.id} | Groups: {groups}")
        return "\n".join(res)
