# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_is_return = fields.Boolean('Is return products', default=False, compute='_compute_is_return')

    @api.depends('origin')
    def _compute_is_return(self):
        for record in self:
            record.x_is_return = False
            if record.origin:
                purchase_order = self.env['purchase.order'].search([('name', '=', self.origin)], limit=1)
                if purchase_order:
                    record.x_is_return = purchase_order.x_is_return

