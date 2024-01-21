# -*- coding: utf-8 -*-
from odoo import _, models, api, fields
from odoo.exceptions import UserError, ValidationError


class PosPromotionConditionCondition(models.Model):
    _name = 'pos.promotion.discount.condition'
    _description = 'PosPromotionDiscountCondition'

    promotion_id = fields.Many2one(comodel_name='pos.promotion',
                                   ondelete='cascade',
                                   string='Promotion')
    category_id = fields.Many2one(comodel_name='pos.category',
                                  string='Pos category')
    product_id = fields.Many2one(comodel_name='product.product',
                                 string='Product')
    qty = fields.Float(string='Quantity', digits='Product Unit of Measure')
    total_amount = fields.Float(string='Total Amount')
    uom_id = fields.Many2one('uom.uom', string='Uom', related='product_id.uom_id')

    @api.onchange('category_id')
    def _onchange_category_id(self):
        if (self.category_id):
            return {'domain': {
                'product_id': [('categ_id', '=', self.category_id.id)]
            }}
        return {'domain': {
            'product_id': []
        }}

    @api.constrains('qty')
    def check_qty(self):
        for rc in self:
            if rc.qty < 0:
                raise UserError(_('You can only create quantity > 0'))