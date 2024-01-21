# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockWarehouseInherit(models.Model):
    _inherit = 'stock.warehouse'

    user_ids = fields.Many2many(comodel_name='res.users', string='Users Access')
    code = fields.Char('Short Name', required=True, help="Short name used to identify your warehouse")
    x_stock_region_id = fields.Many2one('stock.region', string="Stock Region")
    x_location_transfer_id = fields.Many2one('stock.location', string="Location Transfer", required=True)
    x_analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    # def name_get(self):
    #     result = []
    #     for warehouse in self:
    #         result.append((warehouse.id, f'[{warehouse.code}] {warehouse.name}'))
    #     return result
    #
    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=10):
    #     args = args or []
    #     domain = []
    #     if name:
    #         domain = ['|', ('code', operator, name), ('name', operator, name)]
    #     warehouse_id = self.search(domain + args, limit=limit)
    #     return warehouse_id.name_get()