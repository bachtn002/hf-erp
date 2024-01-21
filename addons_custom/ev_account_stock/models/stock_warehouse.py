# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    x_inventory_valuation_group_id = fields.Many2one('inventory.valuation.group', 'Inventory Valuation Group')
