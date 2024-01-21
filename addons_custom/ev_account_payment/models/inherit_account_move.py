# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    x_account_payment_id = fields.Many2one('account.payment','Account Payment')

    def button_cancel(self):
        result = super(AccountMoveInherit, self).button_cancel()
        for move in self:
            if move.x_account_payment_id:
                if move.x_account_payment_id.state != 'cancel':
                    move.x_account_payment_id.state = 'cancel'
        return result

    def button_draft(self):
        result = super(AccountMoveInherit, self).button_draft()
        for move in self:
            if move.x_account_payment_id:
                if move.x_account_payment_id.state != 'draft':
                    move.x_account_payment_id.state = 'draft'
        return result

    def post(self):
        result = super(AccountMoveInherit, self).post()
        for move in self:
            if move.x_account_payment_id:
                if move.x_account_payment_id.state != 'posted':
                    move.x_account_payment_id.state = 'posted'
        return result


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_purchase_order_id = fields.Many2one('purchase.order', "Purchase Order")
    x_accountant_payment_tax_id = fields.Many2one('account.payment.tax', 'Accountant Payment Tax')
    x_accountant_payment_line_id = fields.Many2one('account.payment.line', 'Accountant Payment Line')
