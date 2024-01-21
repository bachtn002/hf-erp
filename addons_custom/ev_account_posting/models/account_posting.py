# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero, pycompat
import math

import logging

_logger = logging.getLogger(__name__)


class AccountPosting(models.Model):
    _name = 'account.posting'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Number Vourcher")
    account_date = fields.Date( string="Account Date", default=fields.Date.context_today, required=True, copy=False, tracking=True)
    date = fields.Date(string="Date", default=fields.Date.context_today, required=True, copy=False, tracking=True)
    description = fields.Char('Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted')
    ], default='draft',copy=False, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    journal_id = fields.Many2one('account.journal', 'Journal', required=True, copy=False)

    account_move_id = fields.Many2one('account.move', 'Move', copy=False)
    line_ids = fields.One2many('account.posting.line', 'account_posting_id', 'Lines')

    def action_compute(self):
        self.line_ids.unlink()
        account_posting_config_ids = self.env['account.posting.config'].search([('active','=', True), ('company_id','=', self.company_id.id)], order='sequence')
        for acc_posting_cf in account_posting_config_ids:
            account_ids = self._get_account_ids(acc_posting_cf.account_from.code)
            for account_id in account_ids:
                value = self._compute_value(account_id, self.account_date)
                if acc_posting_cf.type == 'debit' and value < 0:
                    value = 0
                elif acc_posting_cf.type == 'credit' and value > 0:
                    value = 0

                if acc_posting_cf.type == 'debit':
                    debit_acc_id = acc_posting_cf.account_to.id
                    credit_acc_id = account_id.id
                elif acc_posting_cf.type == 'credit':
                    debit_acc_id = account_id.id
                    credit_acc_id = acc_posting_cf.account_to.id
                else:
                    line_debit_ids = self.env['account.posting.line'].search([('account_posting_id', '=', self.id),
                    ('debit_acc_id','=',acc_posting_cf.account_from.id),('posting_config_id.sequence','<',acc_posting_cf.sequence)])
                    for line_debit_id in line_debit_ids:
                        value += line_debit_id.value
                    line_credit_ids = self.env['account.posting.line'].search([('account_posting_id', '=', self.id),
                    ('credit_acc_id', '=',acc_posting_cf.account_from.id), ('posting_config_id.sequence', '<',acc_posting_cf.sequence)])
                    for line_credit_id in line_credit_ids:
                        value -= line_credit_id.value
                    if value < 0:
                        debit_acc_id = account_id.id
                        credit_acc_id = acc_posting_cf.account_to.id
                    else:
                        debit_acc_id = acc_posting_cf.account_to.id
                        credit_acc_id = account_id.id
                self.env['account.posting.line'].create({
                    'account_posting_id': self.id,
                    'name': acc_posting_cf.description,
                    'debit_acc_id': debit_acc_id,
                    'credit_acc_id': credit_acc_id,
                    'value': abs(value),
                    'posting_config_id': acc_posting_cf.id,
                    'note': ''
                })

    def _compute_value(self, account_id, date):
        self.env.cr.execute("SELECT COALESCE(SUM(balance), 0) FROM account_move_line aml, account_move am WHERE aml.move_id=am.id AND am.state='%s' AND aml.date<='%s' AND aml.account_id=%s" % ('posted', str(date), str(account_id.id)))
        return self.env.cr.fetchone()[0] or 0.000

    def _get_account_ids(self, code):
        return self.env['account.account'].search([('code','=like', code + '%'), ('company_id','=',self.company_id.id)])

    # def action_post2(self):
    #     self.action_compute()
    #     total_value = sum([l.value for l in self.line_ids])
    #     if total_value <= 0:
    #         return
    #     move_lines = []
    #     for l in self.line_ids:
    #         if l.value <= 0:
    #             continue
    #         move_lines.append((0, 0, {
    #             'name': l.name,
    #             'ref': self.name,
    #             'date': self.date,
    #             'account_id': l.debit_acc_id.id,
    #             'debit': l.value,
    #             'credit': 0.000,
    #         }))
    #         move_lines.append((0, 0, {
    #             'name': l.name,
    #             'ref': self.name,
    #             'date': self.date,
    #             'account_id': l.credit_acc_id.id,
    #             'debit': 0.000,
    #             'credit': l.value,
    #         }))
    #     if len(move_lines) > 0:
    #         move_vals = {
    #             'ref': self.name,
    #             'date': self.date,
    #             'journal_id': self.journal_id.id,
    #             'line_ids': move_lines,
    #         }
    #         move_id = self.env['account.move'].create(move_vals)
    #         self.update({'account_move_id': move_id.id})
    #         move_id.post()
    #         self.state = 'posted'

    def action_post(self):
        self.action_compute()
        total_value = sum([l.value for l in self.line_ids])
        if total_value <= 0:
            return
        move_lines = []
        move_vals = {
            'ref': self.name,
            'date': self.date,
            'journal_id': self.journal_id.id,
            'line_ids': move_lines,
        }
        move_id = self.env['account.move'].create(move_vals)
        for l in self.line_ids:
            if l.value <= 0:
                continue
            line_ids = [{
                'name': l.name,
                'ref': self.name,
                'date': self.date,
                'account_id': l.debit_acc_id.id,
                'debit': l.value,
                'credit': 0.000,
                'balance': l.value,
                'move_id': move_id.id
            }, {
                'name': l.name,
                'ref': self.name,
                'date': self.date,
                'account_id': l.credit_acc_id.id,
                'debit': 0.000,
                'credit': l.value,
                'balance': -l.value,
                'move_id': move_id.id
            }]
            move_line_ids = self.env['account.move.line'].create(line_ids)
            l.line_debit_id = move_line_ids[0].id
            l.line_credit_id = move_line_ids[1].id
            move_lines.append(1)
        if len(move_lines) > 0:
            self.update({'account_move_id': move_id.id})
            move_id.post()
            self.check_balance()
            self.state = 'posted'

    def check_balance(self):
        for line_id in self.line_ids.filtered(lambda x: x.value != round(x.value, 2) and x.value != 0):
            balance_account = line_id.value - round(line_id.value)
            value = line_id.line_debit_id.debit + balance_account
            sql = """
                    update account_move_line set credit = %s, balance = %s where id = %s and credit > 0;
                    update account_move_line set debit = %s, balance = %s where id = %s and debit > 0;
            """
            self._cr.execute(sql, (value, -value, line_id.line_credit_id.id, value, value, line_id.line_debit_id.id))

    def action_cancel(self):
        move_ids = self.account_move_id.with_context(force_delete=True)
        move_ids.button_cancel()
        move_ids.unlink()
        self.state = 'draft'

    @api.model
    def create(self, vals_list):
        vals_list['name'] = self.env['ir.sequence'].next_by_code('account_posting_seq')
        vals_list['description'] = 'Kết chuyển lãi lỗ đến ngày ' + vals_list['account_date']
        return super(AccountPosting, self).create(vals_list)

    @api.onchange('account_date')
    def _onchange_account_date(self):
        self.description = 'Kết chuyển lãi lỗ đến ngày ' + str(self.account_date)

    def unlink(self):
        for item in self:
            if item.state == 'posted':
                raise UserError(_('You can only delete when in draft state'))
        super(AccountPosting, self).unlink()


class AccountPostingLine(models.Model):
    _name = 'account.posting.line'

    def _default_company(self):
        return self.env.user.company_id.id

    name = fields.Char(string="Name")
    debit_acc_id = fields.Many2one('account.account', string="Debit Account")
    credit_acc_id = fields.Many2one('account.account', string="Credit Account")
    value = fields.Float(default=0.0, string="Value", digits=(12,10))
    account_posting_id = fields.Many2one('account.posting', 'Posting')
    posting_config_id = fields.Many2one('account.posting.config', 'Account Posting Config')
    note = fields.Char('Note')
    company_id = fields.Many2one('res.company', 'Company', default=_default_company)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency",
                                          readonly=True,
                                          help='Utility field to express amount currency', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id,
                                  help="The optional other currency if it is a multi-currency entry.")
    line_debit_id = fields.Many2one('account.move.line', string="Account Move Debit")
    line_credit_id = fields.Many2one('account.move.line', string="Account Move Credit")