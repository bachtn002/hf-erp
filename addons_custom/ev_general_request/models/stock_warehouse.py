# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    x_general_group_ids = fields.Many2many('general.warehouse.group', 'list_warehouse_group_general', 'warehouse_id', 'group_id',
                                          string='List Group Warehouse')
