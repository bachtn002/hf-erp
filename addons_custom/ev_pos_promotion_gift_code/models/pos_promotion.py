# -*- coding: utf-8 -*-

from odoo import models, fields , api


class PosPromotion(models.Model):
    _inherit = 'pos.promotion'

    type = fields.Selection(selection_add=[('gift_code_total_amount', 'Gift Code Total Amount')])

    promotion_gift_code_total_amount_ids = fields.One2many('pos.promotion.gift.code.total.amount',
                                                           'promotion_id',
                                                           string='Pos Promotion Gift Code Total Amount')

    @api.onchange('type')
    def _onchange_type(self):
        res = super(PosPromotion, self)._onchange_type()
        if self.type != 'gift_code_total_amount':
            self.promotion_gift_code_total_amount_ids = False
        return res
