# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import except_orm
from dateutil.relativedelta import relativedelta


class AccountBalanceVendor(models.Model):
    _name = 'account.balance.vendor'

    name = fields.Char('Name')
    partner_id = fields.Many2one('res.partner', required=1)
    account_id = fields.Many2one('account.account', required=1)
    date = fields.Date(string='Date')
    debit = fields.Float(string='Debit', required=1)
    credit = fields.Float(string='Credit', required=1)
    amount_currency = fields.Float(string='Amount Currency')
    move_id = fields.Many2one('account.move', 'Account Move')
    vendor_code = fields.Char(string='Vendor Code')
    payment_id = fields.Many2one('account.payment', 'Payment')
    invoice_id = fields.Many2one('account.move', 'Invoice')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', 'Currency')
    branch_id = fields.Many2one('res.branch')

    _sql_constraints = [
        ('account_balance_vendor_uniq', 'unique(partner_id, account_id, currency_id)', 'Account balance vendor is unique')
    ]

    @api.onchange('partner_id')
    def onchange_partner(self):
        if self.partner_id:
            self.account_id = self.partner_id.property_account_payable_id
            self.vendor_code = self.partner_id.ref

    @api.model
    def create(self, vals):
        id = super(AccountBalanceVendor, self).create(vals)
        if not id.company_id.x_date_opening_balance:
            raise except_orm(_('Thông báo'),
                             _('Bạn chưa cấu hình ngày chốt số dư!'))
        if not id.company_id.x_account_opening_balance_id:
            raise except_orm(_('Thông báo'),
                             _('Bạn chưa cấu hình tài khoản chốt số dư trong công ty!'))
        account = id.company_id.x_account_opening_balance_id
        date = id.company_id.x_date_opening_balance
        id.date = date
        query = """
                UPDATE account_move_line a
                SET x_update_account_balance = 't', x_value_backup = abs(balance), debit = 0, credit = 0, balance = 0, 
                amount_residual = 0
                FROM account_move b
                WHERE 
                a.move_id = b.id 
                and a.account_id = %d 
                and b."state" = 'posted'
                and a.date <= '%s'
                and a.partner_id = %d
                and NOT EXISTS (SELECT 1 FROM account_balance c WHERE a.move_id = c.move_id);
                UPDATE account_move b
                SET x_update_account_balance = 't'
                FROM account_move_line a
                WHERE 
                a.move_id = b.id 
                and a.account_id = %d 
                and b."state" = 'posted'
                and a.date <= '%s'
                and a.partner_id = %d
                and NOT EXISTS (SELECT 1 FROM account_balance c WHERE a.move_id = c.move_id);"""
        self._cr.execute(
            query % (id.account_id.id, id.date, id.partner_id.id, id.account_id.id, id.date, id.partner_id.id))
        journal_id = self.env['account.journal'].search([('type', '=', 'purchase'),('company_id', '=', id.company_id.id)], limit=1)
        if not journal_id:
            raise except_orm(_('Thông báo'),
                             _('Bạn chưa cấu hình sổ nhật ký có mã KHAC!'))
        move_lines = []
        if id.credit > 0:
            debit_move_vals = {
                'name': id.name,
                'ref': id.name,
                'date': id.date,
                'account_id': account.id,
                'branch_id': id.branch_id.id if id.branch_id else False,
                'debit': id.credit,
                'credit': 0.0,
                'partner_id': id.partner_id.id
            }
            if id.currency_id.id != id.company_id.currency_id.id:
                debit_move_vals['currency_id'] = id.currency_id.id
                debit_move_vals['amount_currency'] = id.amount_currency
            move_lines.append((0, 0, debit_move_vals))
            credit_move_vals = {
                'ref': id.name,
                'name': id.name,
                'date': id.date,
                'account_id': id.account_id.id,
                'branch_id': id.branch_id.id if id.branch_id else False,
                'debit': 0.0,
                'credit': id.credit,
                'partner_id': id.partner_id.id
            }
            if id.currency_id.id != id.company_id.currency_id.id:
                credit_move_vals['currency_id'] = id.currency_id.id
                credit_move_vals['amount_currency'] = -id.amount_currency
            move_lines.append((0, 0, credit_move_vals))
            move_vals = {
                'ref': id.name,
                'date': id.date,
                'company_id': self.company_id.id,
                'branch_id': id.branch_id.id if id.branch_id else False,
                'journal_id': journal_id.id,
                'line_ids': move_lines,
                'partner_id': id.partner_id.id
            }
            move_id = self.env['account.move'].create(move_vals)
            move_id.company_id = id.company_id.id,
            move_id.post()
            id.invoice_id = move_id
            sql = """
                UPDATE account_move_line a
                SET x_update_account_balance = 't', x_value_backup = abs(balance), debit = 0, credit = 0, balance = 0, amount_currency = 0, 
                amount_residual = 0
                where account_id = %d and move_id = %d;
            """
            self._cr.execute(sql % (account.id, move_id.id))
        if id.debit > 0:
            debit_move_vals = {
                'name': id.name,
                'ref': id.name,
                'date': id.date,
                'account_id': id.account_id.id,
                'branch_id': id.branch_id.id if id.branch_id else False,
                'debit': id.debit,
                'credit': 0.0,
                'partner_id': id.partner_id.id
            }
            if id.currency_id.id != id.company_id.currency_id.id:
                debit_move_vals['currency_id'] = id.currency_id.id
                debit_move_vals['amount_currency'] = id.amount_currency
            move_lines.append((0, 0, debit_move_vals))
            credit_move_vals = {
                'ref': id.name,
                'name': id.name,
                'date': id.date,
                'account_id': account.id,
                'branch_id': id.branch_id.id if id.branch_id else False,
                'debit': 0.0,
                'credit': id.debit,
                'partner_id': id.partner_id.id
            }
            if id.currency_id.id != id.company_id.currency_id.id:
                credit_move_vals['currency_id'] = id.currency_id.id
                credit_move_vals['amount_currency'] = -id.amount_currency
            move_lines.append((0, 0, credit_move_vals))
            move_vals = {
                'ref': id.name,
                'date': id.date,
                'company_id': self.company_id.id,
                'branch_id': id.branch_id.id if id.branch_id else False,
                'journal_id': journal_id.id,
                'line_ids': move_lines,
                'partner_id': id.partner_id.id
            }
            move_id = self.env['account.move'].create(move_vals)
            move_id.company_id = id.company_id.id,
            move_id.post()
            id.invoice_id = move_id
            sql = """
                UPDATE account_move_line a
                SET x_update_account_balance = 't', x_value_backup = abs(balance), debit = 0, credit = 0, balance = 0, amount_currency = 0, 
                amount_residual = 0
                where account_id = %d and move_id = %d;
            """
            self._cr.execute(sql % (account.id, move_id.id))
        return id

    def write(self, vals):
        journal_id = self.env['account.journal'].search([('code', '=', 'KHAC'),('company_id','=', self.env.user.company.id)], limit=1)
        account = self.company_id.x_account_opening_balance_id
        move_lines = []
        if 'credit' in vals.keys():
            if vals.get('credit') > 0:
                if self.invoice_id:
                    sql = """
                        DELETE FROM account_move a
                        USING account_balance_vendor b 
                        WHERE 
                        b.invoice_id = a.id 
                        and b.id = %d;
                    """
                    self._cr.execute(sql % (self.id))
                debit_move_vals = {
                    'name': self.name,
                    'ref': self.name,
                    'date': self.date,
                    'account_id': account.id,
                    'branch_id': self.branch_id.id if id.branch_id else False,
                    'debit': vals.get('credit'),
                    'credit': 0.0,
                    'partner_id': self.partner_id.id
                }
                move_lines.append((0, 0, debit_move_vals))
                credit_move_vals = {
                    'ref': self.name,
                    'name': self.name,
                    'date': self.date,
                    'account_id': self.account_id.id,
                    'branch_id': self.branch_id.id if id.branch_id else False,
                    'debit': 0.0,
                    'credit': vals.get('credit'),
                    'partner_id': self.partner_id.id
                }
                move_lines.append((0, 0, credit_move_vals))
                move_vals = {
                    'ref': self.name,
                    'date': self.date,
                    'company_id': self.company_id.id,
                    'branch_id': self.branch_id.id if id.branch_id else False,
                    'journal_id': journal_id.id,
                    'line_ids': move_lines,
                    'partner_id': self.partner_id.id
                }
                move_id = self.env['account.move'].create(move_vals)
                move_id.company_id = self.company_id.id,
                move_id.post()
                self.invoice_id = move_id
                sql = """
                        delete from account_move_line where account_id = %d and move_id = %d;
                    """
                self._cr.execute(sql % (account.id, move_id.id))
        if 'debit' in vals.keys():
            if vals.get('debit') > 0:
                if self.invoice_id:
                    sql = """
                        DELETE FROM account_move a
                        USING account_balance_vendor b 
                        WHERE 
                        b.invoice_id = a.id 
                        and b.id = %d;
                    """
                    self._cr.execute(sql % (self.id))
                debit_move_vals = {
                    'name': self.name,
                    'ref': self.name,
                    'date': self.date,
                    'account_id': self.account_id.id,
                    'branch_id': self.branch_id.id if id.branch_id else False,
                    'debit': vals.get('debit'),
                    'credit': 0.0,
                    'partner_id': self.partner_id.id
                }
                move_lines.append((0, 0, debit_move_vals))
                credit_move_vals = {
                    'ref': self.name,
                    'name': self.name,
                    'date': self.date,
                    'account_id': account.id,
                    'branch_id': self.branch_id.id if id.branch_id else False,
                    'debit': 0.0,
                    'credit': vals.get('debit'),
                    'partner_id': self.partner_id.id
                }
                move_lines.append((0, 0, credit_move_vals))
                move_vals = {
                    'ref': self.name,
                    'date': self.date,
                    'company_id': self.company_id.id,
                    'branch_id': self.branch_id.id if id.branch_id else False,
                    'journal_id': journal_id.id,
                    'line_ids': move_lines,
                    'partner_id': self.partner_id.id
                }
                move_id = self.env['account.move'].create(move_vals)
                move_id.company_id = self.company_id.id,
                move_id.post()
                self.invoice_id = move_id
                sql = """
                        delete from account_move_line where account_id = %d and move_id = %d;
                    """
                self._cr.execute(sql % (account.id, move_id.id))
        return super(AccountBalanceVendor, self).write(vals)

    def unlink(self):
        for line in self:
            if line.invoice_id:
                sql = """
                        DELETE FROM account_move a
                        USING account_balance_vendor b 
                        WHERE 
                        b.invoice_id = a.id 
                        and b.id = %d;
                    """
                self._cr.execute(sql % (line.id))
        return super(AccountBalanceVendor, self).unlink()