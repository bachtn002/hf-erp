from odoo import api, fields, models


class ProductCardAllow(models.Model):
    _name = 'product.card.allow'

    product_id = fields.Many2one('product.template')
    product_allow_id = fields.Many2one('product.product', 'Product')
    maximum_quantity = fields.Integer('Maximum quantity')
