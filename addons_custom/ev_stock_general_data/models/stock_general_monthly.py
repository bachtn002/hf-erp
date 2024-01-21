# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StockGeneralMonthly(models.Model):
    _name = 'stock.general.monthly'
    _description = 'Stock general data monthly'
    _order = 'create_date desc'

    location_id = fields.Many2one('stock.location', 'Location', index=True)
    product_id = fields.Many2one('product.product', 'Product', index=True)
    date = fields.Datetime('Date Sync', index=True)
    month = fields.Integer('Month', index=True)
    year = fields.Integer('Year', index=True)
    qty_begin = fields.Float('Quantity Begin', default=0, digits='Product Unit of Measure')
    qty_in = fields.Float('Quantity In', default=0, digits='Product Unit of Measure')
    qty_out = fields.Float('Quantity Out', default=0, digits='Product Unit of Measure')
    qty_end = fields.Float('Quantity End', default=0, digits='Product Unit of Measure')
    synthesis_id = fields.Many2one('stock.sync.monthly', 'Synthesis Data Monthly', index=True)

    # ngày mặc định theo tháng để check dữ liệu
    date_sync = fields.Datetime('Date', index=True)

    default_code = fields.Char('Default Code', index=True)
    product_name = fields.Char('Product', index=True)
