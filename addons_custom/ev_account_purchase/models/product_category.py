# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductCategory(models.Model):
    _inherit = 'product.category'

    x_account_difference_purchase_id = fields.Many2one('account.account', string='Account Differrence Purchase')
