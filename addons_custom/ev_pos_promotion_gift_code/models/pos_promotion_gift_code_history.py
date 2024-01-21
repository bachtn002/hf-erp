# -*- coding: utf-8 -*-

from odoo import models, fields


class PosPromotionGiftCodeHistory(models.Model):
    _name = 'pos.promotion.gift.code.history'
    _description = 'Pos Promotion Gift Code History'

    pos_promotion_id = fields.Many2one('pos.promotion', string='Pos Promotion')
    pos_order_id = fields.Many2one('pos.order', string='Pos Order')
    gift_code = fields.Char(string='Gift Code')
    phone = fields.Char(string='Phone')
    partner_id = fields.Many2one('res.partner', string='Customer')

    promotion_id = fields.Many2one('pos.promotion', string='Promotion')
