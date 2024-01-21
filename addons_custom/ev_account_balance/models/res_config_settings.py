# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    x_date_opening_balance = fields.Date(related='company_id.x_date_opening_balance', string='Date Opening Balance', readonly=False)