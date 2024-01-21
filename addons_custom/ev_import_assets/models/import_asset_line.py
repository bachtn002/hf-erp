# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError


class ImportAssetLine(models.Model):
    _name = 'import.asset.line'

    name = fields.Char(string='Asset Name')
    code = fields.Char(string='Asset Code')
    quantity = fields.Integer(string="Quantity")
    asset_product_qty_id = fields.Many2one('product.product', string='Asset Code Product Quantity')
    asset_product_id = fields.Many2one('product.product', string='Asset Product')
    asset_model_id = fields.Many2one('account.asset', 'Account Asset')
    price_unit = fields.Float(string='Price')
    date_buy = fields.Date(string='Date Buy')
    date_depreciation_old = fields.Date(string='Date Depreciation Old')
    money_depreciation = fields.Float(string='Money Depreciation')
    value = fields.Float(string='Value Rest')
    method_depreciation = fields.Char(string='Method depreciation')
    method_number = fields.Float(string='Method Number')
    depreciation_number_import = fields.Integer(string='Depreciation Number Import')
    date_depreciation_new = fields.Date(string='Date Depreciation New')
    account_id = fields.Many2one('account.account', string='Account Depreciation')
    account_expense_id = fields.Many2one('account.account', string='Account Expense')
    journal_id = fields.Many2one('account.journal', string='Journal')
    account_analytic_id = fields.Many2one('account.analytic.account', string='Account Analytic')
    account_expense_item_id = fields.Many2one('account.expense.item', string='Account Expense Item')
    account_asset_id = fields.Many2one('account.account', string='Account Depreciation')
    asset_id = fields.Many2one('account.asset', 'Account Asset')
    account_move_id = fields.Many2one('account.move', 'Account Move')
    inventory_loss_account_id = fields.Many2one('account.account', 'Inventory Loss Account')
    account_intital_id = fields.Many2one('account.account', 'Intital Account')
    import_asset_id = fields.Many2one('import.asset', string='Import Asset')
    asset_type = fields.Selection([('assets', 'Assets'), ('tools', 'Tools'), ('expenses', 'Expenses Cost')],
                                  'Asset Type')
