# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import ValidationError, UserError


class PosPromotion(models.Model):
    _inherit = 'pos.promotion'

    type = fields.Selection(selection_add=[
        ('gift_condition', 'Gift Condition')
    ])
    pos_promotion_gift_condition_ids = fields.One2many('pos.promotion.gift.condition.apply', 'promotion_id',
                                                       string="Promotion Gift Condition Apply")
    pos_promotion_gift_apply_ids = fields.One2many('pos.promotion.gift.apply', 'promotion_id',
                                                   string="Promotion Gift Apply")

    @api.constrains('pos_promotion_gift_apply_ids')
    def check_uom_line_apply(self):
        for line in self.pos_promotion_gift_apply_ids:
            if line.qty <= 0:
                raise ValidationError(_("The number of product must be greater than 0!!"))
            else:
                uom_qty = float_round(line.qty, precision_rounding=line.uom_id.rounding, rounding_method='HALF-UP')
                precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                qty = float_round(line.qty, precision_digits=precision_digits, rounding_method='HALF-UP')
                if float_compare(uom_qty, qty, precision_digits=precision_digits) != 0:
                    raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
                                                              defined on the unit of measure "%s". Please change the quantity done or the \
                                                              rounding precision of your unit of measure.') % (
                        line.product_id.display_name, line.uom_id.name))

    @api.constrains('pos_promotion_gift_condition_ids')
    def check_uom_line_condition(self):
        for line in self.pos_promotion_gift_condition_ids:
            if line.qty <= 0:
                raise ValidationError(_("The number of requests must be greater than 0!!"))
            else:
                uom_qty = float_round(line.qty, precision_rounding=line.uom_id.rounding, rounding_method='HALF-UP')
                precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                qty = float_round(line.qty, precision_digits=precision_digits, rounding_method='HALF-UP')
                if float_compare(uom_qty, qty, precision_digits=precision_digits) != 0:
                    raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
                                                                  defined on the unit of measure "%s". Please change the quantity done or the \
                                                                  rounding precision of your unit of measure.') % (
                        line.product_id.display_name, line.uom_id.name))

    @api.onchange('type')
    def _onchange_type(self):
        res = super(PosPromotion, self)._onchange_type()
        if self.type != 'gift_condition':
            self.pos_promotion_gift_condition_ids = False
            self.pos_promotion_gift_apply_ids = False
        return res