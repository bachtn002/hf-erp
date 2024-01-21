# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    x_supply_adjustment_ids = fields.Many2many('supply.adjustment', 'supply_adjustment_warehouse', 'warehouse_id',
                                             'supply_adjustment_id', string='Supply Adjustment')

