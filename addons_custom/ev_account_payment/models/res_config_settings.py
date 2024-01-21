# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    x_account_deposit_id = fields.Many2one('account.account',related='company_id.x_account_deposit_id', string='Account Deposit', readonly=False)