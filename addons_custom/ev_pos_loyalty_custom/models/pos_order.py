# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PosOrderCustom(models.Model):
    _inherit = 'pos.order'

    # @api.model
    # def create_from_ui(self, orders, draft=False):
    #     order_ids = super(PosOrderCustom, self).create_from_ui(orders, draft)
    #     for order in self.sudo().browse([o['id'] for o in order_ids]):
    #         if order.partner_id.x_ecommerce is False:
    #             if order.loyalty_points != 0 and order.partner_id:
    #                 order.partner_id.loyalty_points += order.loyalty_points
    #     return order_ids

