# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class PosOrder(models.Model):
    _inherit = 'pos.order'

    # x_margin = fields.Float('Margin', compute='_compute_margin', store=True, digits='Product Price')
    #
    # @api.depends('lines.margin')
    # def _compute_margin(self):
    #     for order in self:
    #         order.x_margin = sum(order.mapped('lines.x_margin'))


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    x_margin = fields.Float('Margin', compute='_compute_margin_detail', store=True, digits='Product Price')
    x_cost_price = fields.Float(
        'Cost Price', compute='_compute_margin_detail', store=True, digits='Product Price')

    @api.depends('product_id', 'qty', 'price_subtotal')
    def _compute_margin_detail(self):
        for line in self:
            if line.product_id.type != 'service':
                line.x_cost_price = line.product_id.standard_price
                line.x_margin = line.price_subtotal - (line.x_cost_price*line.qty)
