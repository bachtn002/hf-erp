# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    x_process_warehouse = fields.Many2one('stock.location', string="Process Warehouse", default=False, copy=False)

    x_address_warehouse = fields.Char(string='Warehouse Address')
