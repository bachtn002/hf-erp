# -*- coding: utf-8 -*-
from odoo import models, fields, api


class LoyaltyProgramCustom(models.Model):
    _inherit = 'loyalty.program'
    x_point_cost = fields.Float('Point Cost')
    x_discount_amount = fields.Float('Discount Amount')
    product_id = fields.Many2one('product.product', string='Product')