# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    x_general_group_ids = fields.Many2many('general.product.group', 'list_product_group_general', 'product_id',
                                           'group_id',
                                           string='List Group General')

    # x_supply_group_ids = fields.Many2many('supply.product.group', 'list_product_group_supply', 'product_id', 'group_id',
    #                                       string='List Group Supply')
