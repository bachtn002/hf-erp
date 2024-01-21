# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockLocation(models.Model):
    _inherit = 'stock.location'

    x_is_reason = fields.Boolean(string="Is Reason", default=False, copy=False)
    x_type_other = fields.Selection([('incoming','Incoming'),('outgoing','Outgoing')], string="Type Other")
    x_account_expense_item = fields.Many2one('account.expense.item', string='Account Expense Item')

    # @api.model
    # def create(self, vals_list):
    #     if 'x_is_reason' in vals_list.keys():
    #         if vals_list.get('x_is_reason'):
    #             vals_list['location_id'] = self.env.ref('stock.stock_location_locations_virtual', raise_if_not_found=False).id
    #     return super(StockLocation, self).create(vals_list)