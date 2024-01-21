# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StockSyncMonthlyLine(models.Model):
    _name = 'stock.sync.monthly.line'
    _description = 'Stock synthesis data monthly line'
    _order = 'create_date desc'

    synthesis_id = fields.Many2one('stock.sync.monthly', 'Synthesis Data Monthly', index=True)

    location_id = fields.Many2one('stock.location', 'Location', index=True)
    product_id = fields.Many2one('product.product', 'Product', index=True)
    date = fields.Datetime('Date Sync', index=True)
    month = fields.Integer('Month', index=True)
    year = fields.Integer('Year', index=True)
    qty_begin = fields.Float('Quantity Begin', default=0, digits='Product Unit of Measure')
    qty_in = fields.Float('Quantity In', default=0, digits='Product Unit of Measure')
    qty_out = fields.Float('Quantity Out', default=0, digits='Product Unit of Measure')
    qty_end = fields.Float('Quantity End', default=0, digits='Product Unit of Measure')

    # ngày mặc định theo tháng để check dữ liệu
    date_sync = fields.Datetime('Date')
    # thêm uom
    uom_id = fields.Many2one('uom.uom', 'Uom')
    # thêm default_code
    default_code = fields.Char('Default Code', index=True)
    product_name = fields.Char('Product', index=True)
