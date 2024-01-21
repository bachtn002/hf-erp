# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class GeneralWarehouseGroup(models.Model):
    _name = 'general.warehouse.group'
    _description = 'General Warehouse Group'

    code = fields.Char(string='Code Group', required=True)
    name = fields.Char(string='Name Group', required=True)
    warehouse_ids = fields.Many2many('stock.warehouse', 'list_warehouse_group_general', 'group_id', 'warehouse_id',
                                     string='List Warehouse')

    general_ids = fields.Many2many('general.request', 'general_warehouse_group_table', 'group_id', 'general_id',
                                   string='General Request')

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse Supply')
    # order_schedule_ids = fields.Many2many('custom.weekdays', 'general_warehouse_weekdays_rel',
    #                                       'general_warehouse_group_id', 'weekday_id',
    #                                       string='Order Schedule')

    _sql_constraints = [
        ('code_uniq', 'unique (code)', "Code already exists in the system!"),
    ]

    def dowload_template(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/ev_group_sale_request/static/xls/warehouse_group.xlsx'
        }
