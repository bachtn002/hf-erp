# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockLocationInherit(models.Model):
    _inherit = 'stock.location'

    x_code = fields.Char(string="Location's Code")
    x_warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', tracking=True)
    x_region_id = fields.Many2one('stock.region', string="Stock Region", related='x_warehouse_id.x_stock_region_id')
    x_type_warehouse = fields.Selection([
        ('warehouses', 'Warehouses'),
        ('tool_warehouse', 'Tool Warehouse'),
        ('consumable_supplies', 'Consumable Supplies')],
        string='Type warehouse', default='warehouses')
    x_location_old_id = fields.Integer('Location Old Id')

    def write(self, vals):
        res = super(StockLocationInherit, self).write(vals)
        for item in self:
            warehouse_id = item.get_warehouse().id
            if warehouse_id and not item.x_warehouse_id:
                item.x_warehouse_id = warehouse_id
        return res

    @api.model
    def create(self, vals_list):
        res = super(StockLocationInherit, self).create(vals_list)
        warehouse_id = res.get_warehouse().id
        if warehouse_id and not res.x_warehouse_id:
            res.x_warehouse_id = warehouse_id
        return res

    _sql_constraints = [
        ('code_location_company_uniq', 'unique (x_code,company_id)',
         _('The code of the location must be unique per company!'))
    ]

    # def name_get(self):
    #     result = []
    #     for location in self:
    #         result.append((location.id, f'[{location.x_code if location.x_code else ""}] {location.name}'))
    #     return result

    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=10):
    #     args = args or []
    #     domain = []
    #     if name:
    #         domain = ['|', ('x_code', operator, name), ('name', operator, name)]
    #     warehouse_id = self.search(domain + args, limit=limit)
    #     return warehouse_id.name_get()
