# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    x_purchase_line_id = fields.Many2one('purchase.order.line', string='Purchase Line', related='move_id.purchase_line_id', store=True,
                                    readonly=True)