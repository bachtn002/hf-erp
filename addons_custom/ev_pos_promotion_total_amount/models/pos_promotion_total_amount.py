# -*- coding: utf-8 -*-

from odoo import _, models, api, fields
from odoo.exceptions import UserError, ValidationError


class PosPromotionTotalAmount(models.Model):
    _name = 'pos.promotion.total.amount'
    _description = 'PosPromotionTotalAmount'

    promotion_id = fields.Many2one(comodel_name='pos.promotion',
                                   string='Promotion')
    total_amount = fields.Float(digits=(18, 2),
                                string=_('Total amount'),
                                help=_('Total amount of order'))
    discount = fields.Float(digits=(18, 2),
                            string=_('Discount'),
                            default=0.0,
                            help=_('Percent to discount. This value between 0 - 100'),
                            required=True)
    max_discount = fields.Float(digits=(18, 2),
                                string=_('Max Discount'),
                                default=0.0,
                                help=_('Max value to discount. If Max Discount is 0 Nothing to do.'))
    price_discount = fields.Float(string='Price Discount')
    check_discount_price = fields.Selection([
        ('price', _('Price Promotion')),
        ('discount', _('Discount Promotion'))],
        string=_('State Promotion'),
        default='price',
        required=True,
        tracking=True,
        copy=False)

    # @api.constrains('discount')
    # def _constraint_discount(self):
    #     for r in self:
    #         r._discount_factory()

    # @api.constrains('max_discount')
    # def _constraint_max_discount(self):
    #     for r in self:
    #         r._max_discount_factory()

    # @api.onchange('discount')
    # def _onchange_discount(self):
    #     for r in self:
    #         r._discount_factory()

    # @api.onchange('max_discount')
    # def _onchange_max_discount(self):
    #     for r in self:
    #         r._max_discount_factory()

    # def _discount_factory(self):
    #     MIN, MAX = 0, 100
    #     if self.discount < MIN:
    #         self.discount = MIN
    #     elif self.discount > MAX:
    #         self.discount = MAX

    # def _max_discount_factory(self):
    #     if self.max_discount < 0:
    #         self.max_discount = 0
    #     elif self.max_discount > self.total_amount:
    #         self.max_discount = self.total_amount

    @api.constrains('price_discount')
    def check_price_unit(self):
        for rc in self:
            if rc.price_discount < 0:
                raise UserError(_('You can only create price unit > 0'))

    @api.constrains('total_amount')
    def check_total_amount(self):
        for rc in self:
            if rc.total_amount < 0:
                raise UserError(_('You can only create total amount > 0'))

    @api.constrains('max_discount')
    def check_max_discount(self):
        for rc in self:
            if rc.max_discount < 0:
                raise UserError(_('You can only create  max discount > 0'))

    @api.constrains('discount')
    def check_discount(self):
        for rc in self:
            if rc.discount < 0:
                raise UserError(_('You can only create discount > 0'))
            elif rc.discount > 100:
                raise UserError(_('You can only create discount < 100'))
