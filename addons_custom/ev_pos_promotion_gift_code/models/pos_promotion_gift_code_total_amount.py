# -*- coding: utf-8 -*-

from odoo import models, fields, _


class PosPromotionGiftCodeTotalAmount(models.Model):
    _name = 'pos.promotion.gift.code.total.amount'
    _description = 'Pos Promotion Gift Code Total Amount'

    promotion_id = fields.Many2one('pos.promotion', string='Promotion')
    promotion_code_id = fields.Many2one('pos.promotion', string='Promotions Give Code')
    total_amount = fields.Float(digits=(18, 2), string=_('Total amount'))