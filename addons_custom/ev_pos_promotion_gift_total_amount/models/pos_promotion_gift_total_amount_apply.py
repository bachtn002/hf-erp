# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError


class PosPromotionGiftTotalAmountApply(models.Model):
    _name = 'pos.promotion.gift.total.amount.apply'

    promotion_id = fields.Many2one('pos.promotion', string='Promotion')
    product_id = fields.Many2many('product.product', string='Product')
    apply_type = fields.Selection([('one', 'Tặng lẻ'), ('many', 'Tặng gộp')], string='Kiểu tặng')
    qty = fields.Float(string='Quantity', digits='Product Unit of Measure')
    total_amount = fields.Float(string='Total Amount')
    uom_id = fields.Many2one('uom.uom', string=_('Uom'), related='product_id.uom_id')

    @api.constrains('qty')
    def check_qty(self):
        for rc in self:
            if rc.qty < 0:
                raise UserError(_('You can only create quantity > 0'))

    @api.constrains('total_amount')
    def check_total_amount(self):
        for rc in self:
            if rc.total_amount < 0:
                raise UserError(_('You can only create total amount > 0'))
