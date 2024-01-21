# -*- coding: utf-8 -*-

from odoo import _, models, api, fields


class PosPromotion(models.Model):
    _inherit = 'pos.promotion'

    type = fields.Selection(selection_add=[('total_amount', _('Total amount'))])
    pos_promotion_total_amount_ids = fields.One2many(comodel_name='pos.promotion.total.amount',
                                                     inverse_name='promotion_id',
                                                     string='Promotion')

    @api.onchange('type')
    def _onchange_type(self):
        res = super(PosPromotion, self)._onchange_type()
        if self.type != 'total_amount':
            self.pos_promotion_total_amount_ids = False
        return res
