# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_account_expense_item = fields.Many2one('account.expense.item', string='Account Expense Item')

