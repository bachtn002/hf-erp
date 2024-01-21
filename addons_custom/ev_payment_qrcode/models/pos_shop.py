# -*- coding: utf-8 -*-

from odoo import models, fields


class PosShop(models.Model):
    _inherit = 'pos.shop'

    merchant_id = fields.Char(string='Merchant')
