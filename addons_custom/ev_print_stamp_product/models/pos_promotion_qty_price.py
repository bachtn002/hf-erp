# -*- coding: utf-8 -*-

from odoo import models, fields


class PosPromotionQuantityPrice(models.Model):
    _inherit = 'pos.promotion.qty.price'

    note = fields.Text(string='Note')

