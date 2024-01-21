# -*- coding: utf-8 -*-

from odoo import models, fields, _


class GiftCodeProductQtyConditions(models.Model):
    _name = 'gift.code.product.qty.conditions'
    _description = 'Gift Code product Qty Conditions'

    product_id = fields.Many2one('product.product', string='Product')
    min_qty = fields.Float(string='Min quanty')
    promotion_id = fields.Many2one('pos.promotion', string='Promotion')



