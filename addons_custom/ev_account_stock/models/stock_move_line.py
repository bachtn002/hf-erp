# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, except_orm
from odoo.tools import float_is_zero


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    x_unit_cost = fields.Float(string="Unit Cost", compute='_compute_cost', store=True)
    x_value = fields.Float(string='Total cost', compute='_compute_cost', store=True)

    @api.depends('qty_done', 'product_id', 'state', 'move_id.x_unit_cost', 'move_id.x_value')
    def _compute_cost(self):
        for item in self:
            if item.move_id.product_qty != 0:
                balance = item.move_id.x_value/item.move_id.product_qty
                item.x_unit_cost = round(abs(balance))
                item.x_value = round(balance * item.qty_done)