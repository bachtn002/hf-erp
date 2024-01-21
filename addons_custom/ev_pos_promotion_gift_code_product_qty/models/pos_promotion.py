# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosPromotion(models.Model):
    _inherit = 'pos.promotion'

    type = fields.Selection(selection_add=[('gift_code_product_qty', 'Gift Code Product qty')])

    gift_code_product_qty_applies = fields.One2many('gift.code.product.qty.applies', 'promotion_id',
                                                    string='Gift Code product Qty Applies')
    gift_code_product_qty_conditions = fields.One2many('gift.code.product.qty.conditions', 'promotion_id',
                                                       string='Gift Code product Qty Conditions')

    @api.onchange('type')
    def _onchange_type(self):
        res = super(PosPromotion, self)._onchange_type()
        if self.type != 'gift_code_product_qty':
            self.gift_code_product_qty_applies = False
            self.gift_code_product_qty_conditions = False
        return res
