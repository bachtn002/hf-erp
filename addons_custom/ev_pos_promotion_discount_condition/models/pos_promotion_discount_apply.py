# -*- coding: utf-8 -*-
from odoo import _, models, api, fields
from odoo.exceptions import UserError, ValidationError


class PosPromotionDiscountApply(models.Model):
    _name = 'pos.promotion.discount.apply'
    _description = 'PosPromotionDiscountApply'

    promotion_id = fields.Many2one(comodel_name='pos.promotion',
                                   ondelete='cascade',
                                   string='Promotion')
    category_id = fields.Many2one(comodel_name='pos.category',
                                  string='Pos category')
    product_id = fields.Many2one(comodel_name='product.product',
                                 string='Product')
    discount = fields.Float(string='Discount')
    check_discount_price = fields.Selection([
        ('price', _('Price Promotion')),
        ('discount', _('Discount Promotion'))],
        string=_('State Promotion'),
        default='price',
        required=True,
        tracking=True,
        copy=False)
    price_unit = fields.Float(string='Giảm giá')
    apply_type = fields.Selection([('one', 'One'), ('all', 'All')], string='Apply type')

    @api.onchange('category_id')
    def _onchange_category_id(self):
        if (self.category_id):
            return {'domain': {
                'product_id': [('categ_id', '=', self.category_id.id)]
            }}
        return {'domain': {
            'product_id': []
        }}

    @api.constrains('price_unit')
    def check_price_unit(self):
        for rc in self:
            if rc.discount and rc.check_discount_price == 'price':
                rc.discount = False
            if rc.price_unit < 0:
                raise UserError(_('You can only create price unit > 0'))

    @api.constrains('discount')
    def check_discount(self):
        for rc in self:
            if rc.price_unit and rc.check_discount_price == 'discount':
                rc.price_unit = False
            if rc.discount < 0:
                raise UserError(_('You can only create discount > 0'))
            elif rc.discount > 100:
                raise UserError(_('You can only create discount < 100'))
