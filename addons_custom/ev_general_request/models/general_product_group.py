# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class GeneralProductGroup(models.Model):
    _name = 'general.product.group'
    _description = 'General Group Product'

    code = fields.Char(string='Code Group', required=True)
    name = fields.Char(string='Name Group', required=True)
    product_ids = fields.Many2many('product.product', 'list_product_group_general', 'group_id', 'product_id',
                                   string='List Product')

    general_ids = fields.Many2many('general.request', 'general_product_group_table', 'group_id', 'general_id',
                                   string='General Request')

    _sql_constraints = [
        ('code_uniq', 'unique (code)', "Code already exists in the system!"),
    ]

    def dowload_template(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/ev_general_request/static/xls/product_group.xlsx'
        }
