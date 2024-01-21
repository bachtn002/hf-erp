# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    x_code = fields.Char(string='Code')
    x_quantity = fields.Integer(string='Quantity', default=1)
    x_asset_type = fields.Selection([('assets', 'Assets'), ('tools', 'Tools'), ('expenses', 'Expenses Cost')],
                                    'Asset Type')
    x_value_per_period = fields.Monetary(string="Value Per Period", compute='_compute_value_per_period')
    x_value_allocated = fields.Monetary(string="Value Allocated", compute='_compute_value_allocated')
    x_remaining_quantity = fields.Integer(string="Remaining Quantity")
    x_inventory_loss_account_id = fields.Many2one('account.account', 'Inventory Loss Account')

    x_product_asset_id = fields.Many2one('product.product', string='Product Asset')
    x_account_expense_item_id = fields.Many2one('account.expense.item', string='Account Expense Item')

    def _compute_value_per_period(self):
        for item in self:
            item.x_value_per_period = int(item.original_value / item.method_number)

    def _compute_value_allocated(self):
        for item in self:
            item.x_value_allocated = item.original_value - item.value_residual

    @api.model
    def create(self, vals):
        try:
            check_x_code = False
            # # print(vals)
            # print(check_x_code)
            # raise UserError(_('1-1'))
            try:
                if vals['x_code']:
                    return super(AccountAsset, self).create(vals)
                else:
                    check_x_code = True
            except:
                check_x_code = True
            # print(vals)
            # print(check_x_code)
            # raise UserError(_('1-1'))
            if check_x_code == True:
                x_code = ''
                if vals['x_asset_type'] == 'assets':
                    sequence_code = self.env['ir.sequence'].next_by_code('assets.inovice')
                    x_code = 'TS' + datetime.today().strftime('%m%y') + sequence_code
                elif vals['x_asset_type'] == 'tools':
                    sequence_code = self.env['ir.sequence'].next_by_code('tools.inovice')
                    x_code = 'DC' + datetime.today().strftime('%m%y') + sequence_code
                else:
                    sequence_code = self.env['ir.sequence'].next_by_code('expenses.inovice')
                    x_code = 'CP' + datetime.today().strftime('%m%y') + sequence_code
                vals['x_code'] = x_code
            return super(AccountAsset, self).create(vals)
        except Exception as e:
            raise ValidationError(e)

    def _recompute_board(self, depreciation_number, starting_sequence, amount_to_depreciate, depreciation_date,
                         already_depreciated_amount, amount_change_ids):
        move_vals = super(AccountAsset, self)._recompute_board(depreciation_number, starting_sequence,
                                                               amount_to_depreciate, depreciation_date,
                                                               already_depreciated_amount, amount_change_ids)

        return move_vals

    def set_to_draft(self):
        try:
            account_moves = self.env['account.move'].search([('asset_id', '=', self.id)])
            for move in account_moves:
                move.button_cancel()

            if len(account_moves) > 1:
                query = """
                    delete from account_move where id in %s
                """ % (str(tuple(account_moves.ids)))
                self._cr.execute(query)
            elif len(account_moves) == 1:
                query_1 = """
                    delete from account_move where id = %s
                """ % (account_moves.id)
                self._cr.execute(query_1)
            self.write({'state': 'draft'})
        except Exception as e:
            raise ValidationError(e)
