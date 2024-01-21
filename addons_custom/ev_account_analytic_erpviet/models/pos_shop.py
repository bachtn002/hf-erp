# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PosShop(models.Model):
    _inherit = 'pos.shop'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')