# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosPromotionPayment(models.Model):
    _inherit = "pos.payment"

    x_promotion_voucher_id = fields.Many2one('promotion.voucher.line', string='Promotion Voucher')

