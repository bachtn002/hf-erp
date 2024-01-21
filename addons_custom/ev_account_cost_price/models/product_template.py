# -*- coding: utf-8 -*-

from odoo import models, api, fields, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    price_history_ids = fields.One2many('product.price.history', 'product_tmpl_id',string='Product Price History')
    product_price_ids = fields.One2many('product.price', 'product_tmpl_id', string='Product Price')
    x_sequence_calculate = fields.Integer('Sequence Calculate')