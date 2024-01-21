# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    asset_product_id = fields.Many2one('product.product', string='Asset Product')