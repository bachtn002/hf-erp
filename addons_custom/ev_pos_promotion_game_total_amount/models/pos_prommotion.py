# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import ValidationError, UserError


class PosPromotion(models.Model):
    _inherit = 'pos.promotion'

    _sql_constraints = [
        ('game_code_uniq', 'unique (game_code)', 'The game code already exist!')
    ]

    type = fields.Selection(selection_add=[('game_total_amount', 'Game total amount')])
    game_code = fields.Char("Game code")

    promotion_game_total_amount_ids = fields.One2many('pos.promotion.game.total.amount', 'promotion_id',
                                                       string='Pos Promotion Game Total Amount')

    @api.onchange('type')
    def _onchange_type(self):
        res = super(PosPromotion, self)._onchange_type()
        if self.type != 'game_total_amount':
            self.promotion_game_total_amount_ids = False
        return res