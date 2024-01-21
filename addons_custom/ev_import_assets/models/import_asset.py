# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError


class ImportAsset(models.Model):
    _name = 'import.asset'
    _order = 'create_date asc'

    name = fields.Char(string='Name')
    date_import = fields.Date(string='Date import', default=fields.Date.today)

    line_ids = fields.One2many('import.asset.line', 'import_asset_id', string='Asset Line')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('create_asset', 'Create Assets'),
        ('done', 'Done'),
    ], string='State', default='draft')

    @api.onchange('date_import')
    def onchange_date_import(self):
        if self.date_import:
            date = self.date_import.strftime('%d/%m/%Y')
            self.name = _('Import Asset ') + str(date)

    def _create_account_move(self, line):
        move_lines = []
        debit_move_vals = {
            'name': line.name,
            'ref': line.name,
            'date': line.date_depreciation_new,
            'account_id': line.account_asset_id.id,
            'contra_account_id': line.account_intital_id.id,
            'debit': line.value,
            'credit': 0.0,
            'product_id': line.asset_product_id.id,
            'analytic_account_id': line.account_analytic_id.id,
            'quantity': line.quantity
        }
        move_lines.append((0, 0, debit_move_vals))

        # Ghi sổ thu/chi của công ty
        credit_move_vals = {
            'ref': line.name,
            'name': line.name,
            'date': line.date_depreciation_new,
            'account_id': line.account_intital_id.id,
            'contra_account_id': line.account_asset_id.id,
            'debit': 0.0,
            'credit': line.value,
            'product_id': line.asset_product_id.id,
            'analytic_account_id': line.account_analytic_id.id,
            'quantity': line.quantity
        }
        move_lines.append((0, 0, credit_move_vals))
        move_vals = {
            'ref': line.name,
            'date': line.date_depreciation_new,
            'journal_id': line.journal_id.id,
            'line_ids': move_lines,
        }
        move_id = self.env['account.move'].create(move_vals)
        move_id.post()
        return move_id

    def _create_account_asset(self, line):
        #move_line = self.env['account.move.line'].search([('move_id','=', move_id.id), ('account_id.code','!=', '9999')], limit=1)
        vals = {
            'name': line.name,
            'company_id': self.env.user.company_id.id,
            'currency_id': self.env.user.company_id.currency_id.id,
            'account_analytic_id': line.account_analytic_id.id,
            # 'original_move_line_ids': [(6, False, move_line.ids)],
            'state': 'draft',
            'x_quantity': line.quantity,
            'x_remaining_quantity': line.quantity,
            'x_product_asset_id': line.asset_product_id.id,
            'model_id': line.asset_model_id.id if line.asset_model_id else None,
            'x_code': line.code,
            'account_asset_id': line.account_asset_id.id,
            'account_depreciation_id': line.account_id.id,
            'account_depreciation_expense_id': line.account_expense_id.id,
            'journal_id': line.journal_id.id,
            'original_value': line.price_unit,
            'book_value': line.value,
            'value_residual': line.value,
            'already_depreciated_amount_import': line.money_depreciation,
            'acquisition_date': line.date_buy,
            'first_depreciation_date_import': line.date_depreciation_old,
            'first_depreciation_date': line.date_depreciation_new,
            'x_account_expense_item_id': line.account_expense_item_id.id,
            'x_inventory_loss_account_id': line.inventory_loss_account_id.id,
            'depreciation_number_import': line.method_number-line.depreciation_number_import,
            'method_number': line.depreciation_number_import,
            'method_period': '1',
            'asset_type': 'purchase',
            'x_asset_type': line.asset_type
        }
        assets = self.env['account.asset'].create(vals)
        return assets

    def action_create_asset(self):
        self.ensure_one()
        for line in self.line_ids:
            #move_id = self._create_account_move(line)
            asset_id = self._create_account_asset(line)
            #line.account_move_id = move_id
            line.asset_id = asset_id
        self.state = 'create_asset'

    def action_confirm(self):
        self.ensure_one()
        for line in self.line_ids:
            line.asset_id.compute_depreciation_board()
            line.asset_id.validate()
        self.state = 'done'
