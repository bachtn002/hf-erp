# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    x_account_deposit_id = fields.Many2one('account.account', "Account Deposit")
