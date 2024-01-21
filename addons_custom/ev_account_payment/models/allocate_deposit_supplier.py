# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError, except_orm


class AllocateDepositSupplier(models.TransientModel):
    _name = 'allocate.deposit.supplier'

    partner_id = fields.Many2one('res.partner')
    purchase_order_id = fields.Many2one('purchase.order', 'Contract')
    account_move_id = fields.Many2one('account.move', 'Invoice')
    value = fields.Float('Value')
    view_type = fields.Selection([('partner', 'Partner'), ('purchase', 'Purchase')], string='View Type')

    @api.onchange('purchase_order_id')
    def onchange_purchase_order(self):
        if self.purchase_order_id:
            return {
                'domain': {
                    'account_move_id': [('id', 'in', self.purchase_order_id.invoice_ids.ids),
                                          ('state', 'not in', ('draft', 'cancel')),('invoice_payment_state','=','not_paid')]
                }
            }

    @api.onchange('account_move_id')
    def onchange_account_move(self):
        if self.account_move_id:
            if self.account_move_id.invoice_payment_term_id:
                payment_term_line_id = self.env['account.payment.term.line'].search(
                    [('payment_id', '=', self.account_move_id.invoice_payment_term_id.id),
                     ('value', '=', 'percent')], limit=1)
                if payment_term_line_id:
                    self.value = payment_term_line_id.value_amount * self.account_move_id.x_functional_amount_total / 100

    def action_allocate(self):
        if self.purchase_order_id:
            if self.value > self.purchase_order_id.x_remaining_amount:
                raise UserError(_("you cannot allocate with a value greater than the remaining value."))
            if not self.env.user.company_id.x_account_deposit_id:
                raise UserError(_("You have not configured a deposit account."))
            move_id = self._action_create_move(self.env.user.company_id.x_account_deposit_id, self.partner_id.property_account_payable_id, self.value, self.purchase_order_id)
            move_id.post()
            move_line_debit = self.env['account.move.line'].search(
                [('move_id', '=', move_id.id), ('debit', '>', 0),
                 ('parent_state', '=', 'posted'), ('account_internal_type', '=', 'payable'),
                 ('reconciled', '=', False),
                 ('amount_residual', '>', 0)], limit=1)
            self.account_move_id.js_assign_outstanding_line(move_line_debit.id)
            self.purchase_order_id.x_allocated_amount += self.value
            self.purchase_order_id.x_remaining_amount = self.purchase_order_id.x_deposit_amount - self.purchase_order_id.x_allocated_amount
            if self.purchase_order_id.x_remaining_amount > 0:
                self.purchase_order_id.x_status_deposit = 'allocating'
            else:
                self.purchase_order_id.x_status_deposit = 'allocated'

    def _action_create_move(self, account_id, destination_account_id, value, deposit_id):
        journal_id = self.env['account.journal'].search(
            [('type', '=', 'purchase'), ('company_id', '=', self.env.user.company_id.id)], limit=1)
        move_lines = []
        debit_move_vals = {
            'name': deposit_id.origin if deposit_id.origin else deposit_id.name,
            'ref': deposit_id.name,
            'date': fields.Date.today(),
            'account_id': destination_account_id.id,
            'debit': value,
            'credit': 0.0,
            'partner_id': self.partner_id.id,
            'x_purchase_order_id': self.purchase_order_id.id
        }
        move_lines.append((0, 0, debit_move_vals))
        credit_move_vals = {
            'ref': deposit_id.name,
            'name': deposit_id.origin if deposit_id.origin else deposit_id.name,
            'date': fields.Date.today(),
            'account_id': account_id.id,
            'debit': 0.0,
            'credit': value,
            'partner_id': self.partner_id.id,
            'x_purchase_order_id': self.purchase_order_id.id
        }
        move_lines.append((0, 0, credit_move_vals))
        move_vals = {
            'date': fields.Date.today(),
            'journal_id': journal_id.id,
            'line_ids': move_lines,
            'partner_id': self.partner_id.id
        }
        move_id = self.env['account.move'].create(move_vals)
        if move_id:
            return move_id
