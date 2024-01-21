# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    x_enable_combo = fields.Boolean(string='Enable Combo')
    x_edit_combo = fields.Boolean(string='Single Click Product for Edit Combo')

    @api.onchange('x_enable_combo')
    def _onchange_x_enable_combo(self):
        if not self.x_enable_combo:
            self.x_edit_combo = False
