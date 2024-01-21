# -*- coding: utf-8 -*-

from odoo import models, api, fields, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    price_history_ids = fields.One2many('product.price.history', 'product_id',string='Product Price History')
    product_price_ids = fields.One2many('product.price', 'product_id', string='Product Price')

