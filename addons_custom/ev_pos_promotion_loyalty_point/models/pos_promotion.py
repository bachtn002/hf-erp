# -*- coding: utf-8 -*-

from odoo import _, models, api, fields


class PosPromotion(models.Model):
    _inherit = 'pos.promotion'

    type = fields.Selection(selection_add=[('loyalty_point', _('Loyalty point'))])
    pos_promotion_loyalty_point_ids = fields.One2many(comodel_name='pos.promotion.loyalty.point',
                                                     inverse_name='promotion_id',
                                                     string='Promotion')
    is_miniapp_member = fields.Boolean(string='Is miniapp member')

    @api.onchange('type')
    def _onchange_type(self):
        res = super(PosPromotion, self)._onchange_type()
        if self.type != 'loyalty_point':
            self.pos_promotion_loyalty_point_ids = False
        return res
