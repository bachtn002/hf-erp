# -*- coding: utf-8 -*-

from odoo import _, models, api, fields


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    promotion_id = fields.Many2one('pos.promotion',
                                   string=_('Promotion'))
    x_is_price_promotion = fields.Float(_('Price Promotion'))
    x_product_promotion = fields.Char(_('Promotion Product'))
    x_sequence = fields.Integer(_('Sequence'))
    promotion_applied_quantity = fields.Float('Quantity', digits='Product Unit of Measure', default=0)
    amount_promotion_loyalty = fields.Float('Prmotion Loyalty')
    amount_promotion_total = fields.Float('Prmotion Total')

    def _export_for_ui(self, orderline):
        res = super(PosOrderLine, self)._export_for_ui(orderline)
        return res
