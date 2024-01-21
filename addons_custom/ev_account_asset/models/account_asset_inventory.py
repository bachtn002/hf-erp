# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare, float_is_zero, float_round


class AccountAssetInventory(models.Model):
    _name = 'account.asset.inventory'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Asset Inventory')
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account', track_visibility='onchange')
    accounting_date = fields.Datetime('Accounting Date', default=fields.Datetime.now, track_visibility='onchange')
    date = fields.Datetime('Date', default=fields.Datetime.now, track_visibility='onchange')
    lines = fields.One2many('account.asset.inventory.line', 'inventory_id', 'Assets', track_visibility='onchange')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirm'), ('confirm_part', 'Confirm Part'), ('done', 'Done'),
         ('cancel', 'Cancel')],
        string='State', track_visibility='onchange', default='draft')

    def action_confirm(self):
        asset_inventory_id = self.env['account.asset.inventory'].search(
            [('account_analytic_id', '=', self.account_analytic_id.id), ('state', 'in', ['confirm', 'confirm_part'])])
        if len(asset_inventory_id) > 0:
            raise ValidationError('Tại một thời điểm bạn chỉ có một kiểm kê được thực hiện')
        asset_ids = self.env['account.asset'].search(
            [('state', 'in', ['open', 'paused']), ('x_quantity', '>', 0), ('x_remaining_quantity', '>', 0),
             ('account_analytic_id', '=', self.account_analytic_id.id)])
        lines = []
        if len(asset_ids) == 0:
            raise ValidationError('Bộ phận này không có tài sản để thực hiện kiểm kê')
        for asset in asset_ids:
            data = {
                'name': self.name,
                'asset_id': asset.id,
                'asset_code': asset.x_code,
                'uom_id': asset.x_product_asset_id.uom_id.id,
                'inventory_id': self.id,
                'quantity': asset.x_remaining_quantity,
                'actual_quantity': asset.x_remaining_quantity,
                'note': '',
                'price': asset.book_value / asset.x_remaining_quantity,
                'book_value': asset.book_value,
            }
            lines.append((0, 0, data))
        self.lines = lines
        self.state = 'confirm'

    def action_confirm_part(self):
        self.write({'state': 'confirm_part'})

    def action_done(self):
        disposal_date = self.accounting_date or fields.Date.today()
        for line in self.lines:
            balance = line.quantity - line.actual_quantity
            if balance == 0:
                continue
            line.asset_id.x_remaining_quantity = line.actual_quantity
            if balance < 0:
                continue
            if line.book_value == 0:
                continue
            # if line.actual_quantity == 0:
            #     invoice_line = self.env['account.move.line']
            #     line.asset_id.set_to_close(invoice_line_id=invoice_line, date=invoice_line.move_id.invoice_date)
            #     continue

            """ Modifies the duration of asset for calculating depreciation
                    and maintains the history of old values, in the chatter.
                    """

            value_residual = line.asset_id.value_residual - (
                        balance * (line.asset_id.value_residual / line.asset_id.x_quantity))
            old_values = {
                'method_number': line.asset_id.method_number,
                'method_period': line.asset_id.method_period,
                'value_residual': line.asset_id.value_residual,
                'salvage_value': line.asset_id.salvage_value,
            }

            asset_vals = {
                'method_number': len(
                    line.asset_id.depreciation_move_ids.filtered(lambda move: move.state != 'posted')) or 1,
                'method_period': line.asset_id.method_period,
                'value_residual': value_residual,
                'salvage_value': 0,
                'prorata_date': disposal_date
            }

            current_asset_book = line.asset_id.value_residual + line.asset_id.salvage_value
            after_asset_book = value_residual
            increase = after_asset_book - current_asset_book

            new_residual = min(current_asset_book - min(0, line.asset_id.salvage_value),
                               value_residual)
            new_salvage = min(current_asset_book - new_residual, 0)

            # if increase < 0:
            #     if self.env['account.move'].search(
            #             [('asset_id', '=', line.asset_id.id), ('state', '=', 'draft'), ('date', '<=', disposal_date)]):
            #         raise UserError(
            #             'There are unposted depreciations prior to the selected operation date, please deal with them first.')
            #     move = self.env['account.move'].create(self.env['account.move']._prepare_move_for_asset_depreciation_inventory({
            #         'amount': -increase,
            #         'asset_id': line.asset_id,
            #         'move_ref': _('%(name)s: %(asset)s', asset=line.asset_id.name, name=self.name),
            #         'date': disposal_date,
            #         'asset_remaining_value': 0,
            #         'asset_depreciated_value': 0,
            #         'asset_value_change': True,
            #     }))._post()

            asset_vals.update({
                'value_residual': new_residual,
                'salvage_value': new_salvage,
            })
            line.asset_id.write(asset_vals)
            line.asset_id.compute_depreciation_board()
            line.asset_id.children_ids.write({
                'method_number': asset_vals['method_number'],
                'method_period': asset_vals['method_period'],
            })
            for child in line.asset_id.children_ids:
                child.compute_depreciation_board()
            tracked_fields = self.env['account.asset'].fields_get(old_values.keys())
            changes, tracking_value_ids = line.asset_id._message_track(tracked_fields, old_values)
            if changes:
                line.asset_id.message_post(body=_('Depreciation board modified') + '<br>' + 'Kiểm kê tài sản',
                                           tracking_value_ids=tracking_value_ids)
        self.write({'state': 'done'})

    def unlink(self):
        for rc in self:
            if rc.state == 'draft':
                return super(AccountAssetInventory, rc).unlink()
            raise ValidationError('Bạn chỉ xóa được khi ở trạng thái Nháp')

    def action_back(self):
        if self.state == 'confirm':
            self.lines.unlink()
            self.state = 'draft'
        elif self.state == 'confirm_part':
            self.state = 'confirm'
        else:
            return

    def action_cancel(self):
        self.write({'state': 'cancel'})


class AccountAssetInventoryLine(models.Model):
    _name = 'account.asset.inventory.line'

    name = fields.Char('Name')
    asset_id = fields.Many2one('account.asset', 'Asset')
    asset_code = fields.Char('Asset Code')
    uom_id = fields.Many2one('uom.uom', 'Uom')
    inventory_id = fields.Many2one('account.asset.inventory', 'Inventory')
    quantity = fields.Integer('Theoretical Quantity')
    actual_quantity = fields.Integer('Actual Quantity')
    note = fields.Char('Note')
    price = fields.Float('Price')
    book_value = fields.Float('Book Value')


# class AccountMove(models.Model):
#     _inherit = 'account.move'

    # @api.model
    # def _prepare_move_for_asset_depreciation_inventory(self, vals):
    #     missing_fields = set(
    #         ['asset_id', 'move_ref', 'amount', 'asset_remaining_value', 'asset_depreciated_value']) - set(vals)
    #     if missing_fields:
    #         raise UserError(_('Some fields are missing {}').format(', '.join(missing_fields)))
    #     asset = vals['asset_id']
    #     account_analytic_id = asset.account_analytic_id
    #     analytic_tag_ids = asset.analytic_tag_ids
    #     depreciation_date = vals.get('date', fields.Date.context_today(self))
    #     company_currency = asset.company_id.currency_id
    #     current_currency = asset.currency_id
    #     prec = company_currency.decimal_places
    #     amount = current_currency._convert(vals['amount'], company_currency, asset.company_id, depreciation_date)
    #     # Keep the partner on the original invoice if there is only one
    #     partner = asset.original_move_line_ids.mapped('partner_id')
    #     partner = partner[:1] if len(partner) <= 1 else self.env['res.partner']
    #     move_line_1 = {
    #         'name': asset.name,
    #         'partner_id': partner.id,
    #         'account_id': asset.account_depreciation_id.id,
    #         'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
    #         'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
    #         'analytic_account_id': account_analytic_id.id if asset.asset_type == 'sale' else False,
    #         'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if asset.asset_type == 'sale' else False,
    #         'currency_id': current_currency.id,
    #         'amount_currency': -vals['amount'],
    #     }
    #     move_line_2 = {
    #         'name': asset.name,
    #         'partner_id': partner.id,
    #         'account_id': asset.company_id.loss_account_id.id,
    #         'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
    #         'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
    #         'analytic_account_id': account_analytic_id.id if asset.asset_type in ('purchase', 'expense') else False,
    #         'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if asset.asset_type in (
    #             'purchase', 'expense') else False,
    #         'currency_id': current_currency.id,
    #         'amount_currency': vals['amount'],
    #     }
    #     move_vals = {
    #         'ref': vals['move_ref'],
    #         'partner_id': partner.id,
    #         'date': depreciation_date,
    #         'journal_id': asset.journal_id.id,
    #         'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
    #         'asset_id': asset.id,
    #         'asset_remaining_value': vals['asset_remaining_value'],
    #         'asset_depreciated_value': vals['asset_depreciated_value'],
    #         'amount_total': amount,
    #         'name': '/',
    #         'asset_value_change': vals.get('asset_value_change', False),
    #         'move_type': 'entry',
    #         'currency_id': current_currency.id,
    #     }
    #     return move_vals
