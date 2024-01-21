# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class SupplyProductGroup(models.Model):
    _name = 'supply.product.group'
    _description = 'Supply Group Product'

    code = fields.Char(string='Code Group', required=True)
    name = fields.Char(string='Name Group', required=True)
    product_ids = fields.Many2many('product.product', 'list_product_group_supply', 'group_id', 'product_id',
                                    string='List Product')
    supply_ids = fields.Many2many('supply.request', 'supply_product_group_table', 'group_id', 'supply_id',
                                   string='Supply Request')


    _sql_constraints =  [
        ('code_uniq', 'unique (code)', "Code already exists in the system!"),
    ]

    def dowload_template(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/ev_group_sale_request/static/xls/product_group.xlsx'
        }
