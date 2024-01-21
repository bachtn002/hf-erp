# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleOnlineDiscountOnProduct(models.Model):
    _name = 'sale.online.discount.on.product'
    _description = 'Sale Online Discount On Product'

    product_code = fields.Char(string='Product Code')
    discount_on_product = fields.Float(string='Discount On Product')
    promotion_code = fields.Char(string='Promotion Code')
    promotion_id = fields.Char(string='Promotion Id')
    sale_online_id = fields.Many2one('sale.online', string='Sale Online')
