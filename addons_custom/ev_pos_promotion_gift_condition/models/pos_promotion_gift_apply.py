# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError


class PosPromotionGiftApply(models.Model):
    _name = 'pos.promotion.gift.apply'

    promotion_id = fields.Many2one('pos.promotion', string='Promotion')
    category_id = fields.Many2one('pos.category', string='Product Category')
    product_id = fields.Many2one('product.product', string='Product')
    qty = fields.Float(string='Quantity', digits='Product Unit of Measure')
    uom_id = fields.Many2one('uom.uom', string=_('Uom'), related='product_id.uom_id')

    @api.constrains('qty')
    def check_qty(self):
        for rc in self:
            if rc.qty < 0:
                raise UserError(_('You can only create quantity > 0'))
