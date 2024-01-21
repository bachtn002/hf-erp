# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleOnlineDiscountOnBill(models.Model):
    _name = 'sale.online.discount'
    _description = 'Sale Online Discount'

    promotion_code = fields.Char(string='Promotion Code')
    promotion_id = fields.Many2one('pos.promotion', string='Promotion')
    sale_online_id = fields.Many2one('sale.online', string='Sale Online')
    discount_type = fields.Selection([
        ('on_bill', 'On Bill'),
        ('on_product', 'On Product')
    ], string='Discount Type')
    product_code = fields.Char(string='Product Code')
    discount_amount = fields.Float(string='Discount Amount')
