from odoo import api, fields, models


class ProductCategoryCardAllow(models.Model):
    _name = 'product.category.card.allow'

    product_id = fields.Many2one('product.template')
    product_category_allow_id = fields.Many2one('product.category', 'Product category')
    maximum_quantity = fields.Integer('Maximum quantity')
