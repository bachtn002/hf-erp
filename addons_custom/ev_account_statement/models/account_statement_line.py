# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountStatementLine(models.Model):
    _name = 'account.statement.line'

    account_statement_id = fields.Many2one('account.statement', string='Account Statement ID', required=True)

    code = fields.Char(string='Code Deal')
    name = fields.Char(string='License')
    date = fields.Date(string='Date', required=True)
    description = fields.Text(string='Description', required=True)
    amount = fields.Float(string='Amount', required=True)

    account_analytic_id = fields.Many2one('account.analytic.account', string='Account Analytic Account ID',
                                          required=True)
    account_move_id = fields.Many2one('account.move', 'Account Move')
    account_id = fields.Many2one('account.account', 'Account Account')
