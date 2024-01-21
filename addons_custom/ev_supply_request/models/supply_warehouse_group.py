# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class SupplyWarehouseGroup(models.Model):
    _name = 'supply.warehouse.group'
    _description = 'Supply Warehouse Group'

    code = fields.Char(string='Code Group', required=True)
    name = fields.Char(string='Name Group', required=True)
    warehouse_ids = fields.Many2many('stock.warehouse', 'list_warehouse_group_supply', 'group_id', 'warehouse_id',
                                    string='List Supply Warehouse')
    supply_ids = fields.Many2many('supply.request', 'supply_warehouse_group_table', 'group_id', 'supply_id',
                                   string='Supply Request')

    _sql_constraints =  [
        ('code_uniq', 'unique (code)', "Code already exists in the system!"),
    ]

    def dowload_template(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/ev_supply_request/static/template/warehouse_group.xlsx'
        }