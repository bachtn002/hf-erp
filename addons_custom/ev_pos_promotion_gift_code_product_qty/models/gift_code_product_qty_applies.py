# -*- coding: utf-8 -*-
from odoo import api, fields, models


class GiftCodeProductQtyApplies(models.Model):
    _name = 'gift.code.product.qty.applies'
    _description = 'Gift Code product Qty Applies'

    promotion_gift_id = fields.Many2one('pos.promotion', string='Promotion Gift')
    gift_qty = fields.Float(string='Gift quanty')
    promotion_id = fields.Many2one('pos.promotion', string='Promotion')
