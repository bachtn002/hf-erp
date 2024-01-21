# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    x_date_opening_balance = fields.Date('Date Opening Balance')
    x_account_opening_balance_id = fields.Many2one('account.account', "Account Opening Balance")
