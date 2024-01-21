# -*- coding: utf-8 -*-
from odoo import _, models, api, fields


class PosPromotionGameTotalAmount(models.Model):
    _name = 'pos.promotion.game.total.amount'
    _description = 'Pos Promotion Game Total Amount'

    promotion_id = fields.Many2one('pos.promotion', string='Promotion')
    game_code = fields.Char(related='promotion_id.game_code', string='Game code')
    game_turn = fields.Integer(string='Game turn reward', required=1)
    total_amount = fields.Float(string='Total Amount', required=1)

