# -*- coding: utf-8 -*-
import odoo.tools.config as config

from odoo import models, fields, api, exceptions


class StockQuantCurrentLine(models.TransientModel):
    _name = 'stock.quant.current.line'

    product_id = fields.Many2one('product.product', string='Products')
    uom_id = fields.Many2one('uom.uom', string='Uom')
    quantity = fields.Float(string='Quantity', digits='Product Unit of Measure')
    stock_quant_current_id = fields.Many2one('stock.quant.current', '')