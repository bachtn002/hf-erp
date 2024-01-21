# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class PosShop(models.Model):
    _inherit = 'pos.shop'

    cash_fund_balance = fields.Integer('Cash Fund Balance')