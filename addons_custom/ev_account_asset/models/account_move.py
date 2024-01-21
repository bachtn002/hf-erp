# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero, float_round

from datetime import datetime


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _auto_create_asset(self):
        try:
            create_list = []
            invoice_list = []
            auto_validate = []
            check_invoice = False
            account_analytic_id = self.env['account.analytic.account']
            asset_type = ''
            asset_from = ''
            x_product_asset_id = ''
            for move in self:
                if move.is_invoice():
                    check_invoice = True

                for move_line in move.line_ids.filtered(lambda line: not (move.move_type in (
                        'out_invoice', 'out_refund') and line.account_id.user_type_id.internal_group == 'asset')):
                    if check_invoice:
                        if (
                                move_line.account_id
                                and (move_line.account_id.can_create_asset)
                                and move_line.account_id.create_asset != "no"
                                and not move.reversed_entry_id
                                and not (move_line.currency_id or move.currency_id).is_zero(move_line.price_total)
                                and not move_line.asset_ids
                        ):
                            if not move_line.name:
                                raise UserError(
                                    _('Journal Items of {account} should have a label in order to generate an asset').format(
                                        account=move_line.account_id.display_name))
                            if move_line.account_id.multiple_assets_per_line:
                                # decimal quantities are not supported, quantities are rounded to the lower int
                                units_quantity = max(1, int(move_line.quantity))
                            else:
                                units_quantity = 1
                            vals = {
                                'name': move_line.name,
                                'company_id': move_line.company_id.id,
                                'currency_id': move_line.company_currency_id.id,
                                'account_analytic_id': move_line.analytic_account_id.id,
                                'analytic_tag_ids': [(6, False, move_line.analytic_tag_ids.ids)],
                                'original_move_line_ids': [(6, False, move_line.ids)],
                                'state': 'draft',
                                'x_quantity': move_line.quantity,
                                'x_remaining_quantity': move_line.quantity,
                                'x_product_asset_id': move_line.product_id.id,
                            }
                            model_id = move_line.account_id.asset_model
                            asset_type = model_id.x_asset_type
                            x_code = ''
                            account_analytic_id = move_line.analytic_account_id
                            if asset_type == 'assets':
                                sequence_code = self.env['ir.sequence'].next_by_code('assets.inovice')
                                x_code = 'TS' + datetime.today().strftime('%m%y') + sequence_code
                            elif asset_type == 'tools':
                                sequence_code = self.env['ir.sequence'].next_by_code('tools.inovice')
                                x_code = 'DC' + datetime.today().strftime('%m%y') + sequence_code
                            else:
                                sequence_code = self.env['ir.sequence'].next_by_code('expenses.inovice')
                                x_code = 'CP' + datetime.today().strftime('%m%y') + sequence_code
                            if model_id:
                                vals.update({
                                    'model_id': model_id.id,
                                    'x_inventory_loss_account_id': model_id.x_inventory_loss_account_id.id,
                                    'x_account_expense_item_id': model_id.x_account_expense_item_id.id,
                                    'x_asset_type': model_id.x_asset_type if model_id.x_asset_type else 'expenses',
                                    'x_code': x_code,
                                    'account_analytic_id': account_analytic_id.id,
                                })
                            else:
                                vals.update({
                                    'x_inventory_loss_account_id': model_id.x_inventory_loss_account_id.id,
                                    'x_account_expense_item_id': model_id.x_account_expense_item_id.id,
                                    'x_asset_type': 'expenses',
                                    'x_code': x_code,
                                    'account_analytic_id': account_analytic_id.id,
                                })
                            auto_validate.extend([move_line.account_id.create_asset == 'validate'] * units_quantity)
                            invoice_list.extend([move] * units_quantity)
                            create_list.extend([vals] * units_quantity)

                    elif move.stock_move_id:
                        if (
                                move_line.account_id
                                and (move_line.account_id.can_create_asset)
                                and move_line.account_id.create_asset != "no"
                                and not move.reversed_entry_id
                                and not (move_line.currency_id or move.currency_id).is_zero(move_line.debit)
                                and not move_line.asset_ids
                        ):
                            if not move_line.name:
                                raise UserError(
                                    _('Journal Items of {account} should have a label in order to generate an asset').format(
                                        account=move_line.account_id.display_name))
                            if move_line.account_id.multiple_assets_per_line:
                                # decimal quantities are not supported, quantities are rounded to the lower int
                                units_quantity = max(1, int(move_line.quantity))
                            else:
                                units_quantity = 1
                            vals = {
                                'name': move_line.name,
                                'company_id': move_line.company_id.id,
                                'currency_id': move_line.company_currency_id.id,
                                'account_analytic_id': move_line.analytic_account_id.id,
                                'analytic_tag_ids': [(6, False, move_line.analytic_tag_ids.ids)],
                                'original_move_line_ids': [(6, False, move_line.ids)],
                                'state': 'draft',
                                'x_quantity': abs(move_line.quantity),
                                'x_remaining_quantity': abs(move_line.quantity),
                                'x_product_asset_id': move_line.product_id.id,
                            }
                            model_id = move_line.account_id.asset_model
                            asset_type = model_id.x_asset_type
                            x_code = ''
                            account_analytic_id = move_line.analytic_account_id
                            x_product_asset_id = move_line.product_id.default_code
                            if asset_type == 'assets':
                                sequence_code = self.env['ir.sequence'].next_by_code('assets.picking')
                                x_code = 'TS-' + x_product_asset_id + '.' + sequence_code
                            elif asset_type == 'tools':
                                sequence_code = self.env['ir.sequence'].next_by_code('tools.picking')
                                x_code = 'DC-' + x_product_asset_id + '.' + sequence_code
                            else:
                                sequence_code = self.env['ir.sequence'].next_by_code('expenses.picking')
                                x_code = 'CP-' + x_product_asset_id + '.' + sequence_code
                            if model_id:
                                vals.update({
                                    'model_id': model_id.id,
                                    'x_inventory_loss_account_id': model_id.x_inventory_loss_account_id.id,
                                    'x_account_expense_item_id': model_id.x_account_expense_item_id.id,
                                    'x_asset_type': model_id.x_asset_type if model_id.x_asset_type else 'expenses',
                                    'x_code': x_code,
                                    'account_analytic_id': account_analytic_id.id,
                                })
                            else:
                                vals.update({
                                    'x_inventory_loss_account_id': model_id.x_inventory_loss_account_id.id,
                                    'x_account_expense_item_id': model_id.x_account_expense_item_id.id,
                                    'x_asset_type': 'expenses',
                                    'x_code': x_code,
                                    'account_analytic_id': account_analytic_id.id,
                                })
                            auto_validate.extend([move_line.account_id.create_asset == 'validate'] * units_quantity)
                            invoice_list.extend([move] * units_quantity)
                            create_list.extend([vals] * units_quantity)

            assets = self.env['account.asset'].create(create_list)

            for asset, vals, invoice, validate in zip(assets, create_list, invoice_list, auto_validate):
                if 'model_id' in vals:
                    account_analytic_id = asset.account_analytic_id
                    asset._onchange_model_id()
                    if account_analytic_id:
                        asset.account_analytic_id = account_analytic_id
                    if validate:
                        asset.validate()
                if invoice and check_invoice:
                    asset_name = {
                        'purchase': _('Asset'),
                        'sale': _('Deferred revenue'),
                        'expense': _('Deferred expense'),
                    }[asset.asset_type]
                    msg = _('%s created from invoice') % (asset_name)
                    msg += ': <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>' % (invoice.id, invoice.name)
                    asset.message_post(body=msg)
            return assets
        except Exception as e:
            raise ValidationError(e)

    @api.model
    def _prepare_move_for_asset_depreciation(self, vals):
        try:
            missing_fields = set(
                ['asset_id', 'move_ref', 'amount', 'asset_remaining_value', 'asset_depreciated_value']) - set(vals)
            if missing_fields:
                raise UserError(_('Some fields are missing {}').format(', '.join(missing_fields)))
            asset = vals['asset_id']
            account_analytic_id = asset.account_analytic_id
            x_account_expense_item_id = asset.x_account_expense_item_id
            analytic_tag_ids = asset.analytic_tag_ids
            depreciation_date = vals.get('date', fields.Date.context_today(self))
            company_currency = asset.company_id.currency_id
            current_currency = asset.currency_id
            prec = company_currency.decimal_places
            amount = current_currency._convert(vals['amount'], company_currency, asset.company_id, depreciation_date)
            # Keep the partner on the original invoice if there is only one
            partner = asset.original_move_line_ids.mapped('partner_id')
            partner = partner[:1] if len(partner) <= 1 else self.env['res.partner']
            move_line_1 = {
                'name': asset.name,
                'partner_id': partner.id,
                'account_id': asset.account_depreciation_id.id,
                'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'analytic_account_id': account_analytic_id.id,
                'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if asset.asset_type == 'sale' else False,
                'currency_id': current_currency.id,
                'amount_currency': -vals['amount'],
                'x_account_expense_item_id': x_account_expense_item_id.id
            }
            move_line_2 = {
                'name': asset.name,
                'partner_id': partner.id,
                'account_id': asset.account_depreciation_expense_id.id,
                'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'analytic_account_id': account_analytic_id.id if asset.asset_type in ('purchase', 'expense') else False,
                'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if asset.asset_type in (
                    'purchase', 'expense') else False,
                'currency_id': current_currency.id,
                'amount_currency': vals['amount'],
                'x_account_expense_item_id': x_account_expense_item_id.id
            }
            move_vals = {
                'ref': vals['move_ref'],
                'partner_id': partner.id,
                'date': depreciation_date,
                'journal_id': asset.journal_id.id,
                'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
                'asset_id': asset.id,
                'asset_remaining_value': vals['asset_remaining_value'],
                'asset_depreciated_value': vals['asset_depreciated_value'],
                'amount_total': amount,
                'name': '/',
                'asset_value_change': vals.get('asset_value_change', False),
                'move_type': 'entry',
                'currency_id': current_currency.id,
            }
            return move_vals
        except Exception as e:
            raise ValidationError(e)
