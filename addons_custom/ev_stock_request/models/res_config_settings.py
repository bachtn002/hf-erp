# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    x_auto_create_transfer = fields.Boolean(related='company_id.x_auto_create_transfer', string='Auto create transfer', readonly=False)