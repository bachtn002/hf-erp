# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    x_supply_group_ids = fields.Many2many('supply.warehouse.group', 'list_warehouse_group_supply', 'warehouse_id', 'group_id',
                                          string='List Group Warehouse')
