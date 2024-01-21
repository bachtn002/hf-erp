# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError


class PosPromotionTotalPriceBuyOtherProduct(models.Model):
    _name = 'pos.promotion.total.price.buy.other.product'

    promotion_id = fields.Many2one('pos.promotion', string='Promotion')
    product_id = fields.Many2one('product.product', string='Sản phẩm áp dụng')
    qty = fields.Float(string='Số lượng', digits='Product Unit of Measure')
    price_unit = fields.Float(string='Giảm giá')
    total_price = fields.Float(string='Tổng giá trị đơn hàng')
    discount = fields.Float(digits=(18, 2), string=_('Chiết khấu'), default=0.0,
                            help=_('Percent to discount. This value between 0 - 100'), required=True)
    check_discount_price = fields.Selection([
        ('price', _('Price Promotion')),
        ('discount', _('Discount Promotion'))],
        string=_('State Promotion'),
        default='price',
        required=True,
        tracking=True,
        copy=False)
    uom_id = fields.Many2one('uom.uom', string=_('Uom'), related='product_id.uom_id')
    # @api.constrains('discount')
    # def _constraint_discount(self):
    #     for r in self:
    #         r._discount_factory()
    #
    # @api.onchange('discount')
    # def _onchange_discount(self):
    #     for r in self:
    #         r._discount_factory()

    def _discount_factory(self):
        MIN, MAX = 0, 100
        if self.discount < MIN:
            self.discount = MIN
        elif self.discount > MAX:
            self.discount = MAX

    @api.constrains('price_unit')
    def check_price_unit(self):
        for rc in self:
            if rc.price_unit < 0:
                raise UserError(_('You can only create price unit > 0'))

    @api.constrains('qty')
    def check_qty(self):
        for rc in self:
            if rc.qty < 0:
                raise UserError(_('You can only create quantity > 0'))

    @api.constrains('total_price')
    def check_total_price(self):
        for rc in self:
            if rc.total_price < 0:
                raise UserError(_('You can only create total price > 0'))

    @api.constrains('discount')
    def check_discount(self):
        for rc in self:
            if rc.discount < 0:
                raise UserError(_('You can only create discount > 0'))
            elif rc.discount > 100:
                raise UserError(_('You can only create discount < 100'))
