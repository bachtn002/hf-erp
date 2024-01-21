# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError


class PosPromotionQuantityPrice(models.Model):
    _name = 'pos.promotion.qty.price'

    promotion_id = fields.Many2one('pos.promotion', string='Promotion')
    category_id = fields.Many2one('pos.category', string='Product Category')
    product_id = fields.Many2one('product.product', string='Apply Product')
    qty = fields.Float(string='Quantity', digits='Product Unit of Measure')
    price_unit = fields.Float(string='Price Unit')
    discount = fields.Float(string='Discount')
    check_discount_price = fields.Selection([
        ('price', _('Price Promotion')),
        ('discount', _('Discount Promotion'))],
        string=_('State Promotion'),
        default='price',
        required=True,
        tracking=True,
        copy=False)
    uom_id = fields.Many2one('uom.uom', string=_('Uom'), related='product_id.uom_id')

    @api.constrains('price_unit')
    def check_price_unit(self):
        for rc in self:
            if rc.price_unit < 0:
                raise UserError(_('You can only create price unit > 0'))

    # @api.constrains('qty')
    # def check_qty(self):
    #     for rc in self:
    #         if rc.qty < 0:
    #             raise UserError(_('You can only create quantity > 0'))

    @api.constrains('discount')
    def check_discount(self):
        for rc in self:
            if rc.discount < 0:
                raise UserError(_('You can only create discount > 0'))
            elif rc.discount > 100:
                raise UserError(_('You can only create discount < 100'))
