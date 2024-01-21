# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SupplyAdjustment(models.Model):
    _name = 'supply.adjustment'

    name = fields.Char(string='Name Adjustment', required=True)
    region_ids = fields.Many2many('stock.region', 'supply_adjustment_region', 'supply_adjustment_id', 'region_id',
                                  string='Region')
    warehouse_ids = fields.Many2many('stock.warehouse', 'supply_adjustment_warehouse', 'supply_adjustment_id',
                                     'warehouse_id', string='Warehouse')
    product_ids = fields.Many2many('product.product', 'supply_adjustment_product', 'supply_adjustment_id',
                                   'product_id', string='Product')

    supply_type = fields.Selection([
        ('warehouse', 'Warehouse'),
        ('purchase', 'Purchase'),
        ('stop_supply', 'Stop Supply')],
        string='Supply Product', default=False)

