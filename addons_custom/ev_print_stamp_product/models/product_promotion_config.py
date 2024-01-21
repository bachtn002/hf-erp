from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductPromotionConfig(models.Model):
    _name = 'product.promotion.config'
    _rec_name = 'product_id'

    product_id = fields.Many2one(comodel_name='product.product', string="Product ID", required=True)
    name_above = fields.Char(string="Name above", size = 34)
    name_below = fields.Char(string="Name below", size = 34)

    _sql_constraints = [
        ('product_id_uniq', 'unique(product_id)', 'Product id must be unique !')
    ]

    