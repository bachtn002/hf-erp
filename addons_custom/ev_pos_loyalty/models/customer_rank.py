# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CustomerRank(models.Model):
    _name = 'customer.rank'
    _order = 'create_date ASC'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Customer rank'

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    point = fields.Float(string="Point")
    discount = fields.Float(string="Discount")
    product_id = fields.Many2one('product.product', string="Promotional Products ", domain=[('type','=', 'service')])
    categories_ids = fields.Many2many('pos.category', string="Categories not apply for pos loyalty",
                                      relation='customer_rank_category_rel')
    product_ids = fields.Many2many('product.product', string="Products not apply for pos loyalty",
                                   relation='customer_rank_product_rel')
