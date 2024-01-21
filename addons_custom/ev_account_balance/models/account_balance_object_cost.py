# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm


class AccountBalanceObjectCost(models.Model):
    _name = 'account.balance.object.cost'
    _description = 'Account Balance Object Model'

    def _domain_account(self):
        ids = []
        accounts = self.env['account.account'].search([('company_id', '=', self.env.company.id)], order='id')
        for a in accounts:
            ids.append(a.id)
        return [('id', 'in', ids)]

    name = fields.Char('Name')
    account_id = fields.Many2one('account.account', string="Account", required=1, domain=_domain_account)
    debit = fields.Float("Debit", required=1)
    credit = fields.Float("Credit", required=1)
    date = fields.Date(string='Date')
    move_id = fields.Many2one('account.move', 'Account Move')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    object_cost_id = fields.Many2one('object.cost', 'Object cost', required=1)
    branch_id = fields.Many2one('res.branch')


    _sql_constraints = [
        ('account_balance_x_uniq', 'unique(account_id,object_cost_id)', 'Account balance is unique')
    ]

    @api.model
    def create(self, vals):
        id = super(AccountBalanceObjectCost, self).create(vals)
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
        and object_cost_id = %d
        and b."state" = 'posted'
        and a.date <= '%s'
        and NOT EXISTS (SELECT 1 FROM account_balance c WHERE a.move_id = c.move_id);
        UPDATE account_move b
        SET x_update_account_balance = 't'
        FROM account_move_line a
        WHERE 
        a.move_id = b.id 
        and a.account_id = %d 
        and object_cost_id = %d
        and b."state" = 'posted'
        and a.date <= '%s'
        and NOT EXISTS (SELECT 1 FROM account_balance c WHERE a.move_id = c.move_id);"""
        self._cr.execute(query % (id.account_id.id, id.object_cost_id.id, id.date, id.account_id.id,
                                  id.object_cost_id.id, id.date))
        move_lines = []
        journal_id = self.env['account.journal'].search([('code', '=', 'KHAC'),('company_id','=', self.env.user.company.id)], limit=1)
        if not journal_id:
            raise except_orm(_('Thông báo'),
                             _('Bạn chưa cấu hình sổ nhật ký có mã KHAC!'))
        if id.debit > 0:
            debit_move_vals = {
                'name': id.name,
                'ref': id.name,
                'date': id.date,
                'account_id': id.account_id.id,
                'branch_id': id.branch_id.id if id.branch_id else False,
                'debit': id.debit,
                'credit': 0.0,
                'object_cost_id': id.object_cost_id.id
            }
            move_lines.append((0, 0, debit_move_vals))
            credit_move_vals = {
                'ref': id.name,
                'name': id.name,
                'date': id.date,
                'account_id': account.id,
                'branch_id': id.branch_id.id if id.branch_id else False,
                'debit': 0.0,
                'credit': id.debit,
                'object_cost_id': id.object_cost_id.id
            }
            move_lines.append((0, 0, credit_move_vals))
            move_vals = {
                'ref': id.name,
                'date': id.date,
                'company_id': self.company_id.id,
                'branch_id': id.branch_id.id if id.branch_id else False,
                'journal_id': journal_id.id,
                'line_ids': move_lines,
            }
            move_id = self.env['account.move'].create(move_vals)
            move_id.company_id = id.company_id.id,
            move_id.post()
            id.move_id = move_id
            sql = """
                UPDATE account_move_line a
                SET x_update_account_balance = 't', x_value_backup = abs(balance), debit = 0, credit = 0, balance = 0, amount_currency = 0, 
                amount_residual = 0
                where account_id = %d and move_id = %d;
            """
            self._cr.execute(sql % (account.id, move_id.id))
        if id.credit > 0:
            # Ghi sổ thu/chi của công ty
            credit_move_vals = {
                'ref': id.name,
                'name': id.name,
                'date': id.date,
                'account_id': id.account_id.id,
                'branch_id': id.branch_id.id if id.branch_id else False,
                'debit': 0.0,
                'credit': id.credit,
                'object_cost_id': id.object_cost_id.id
            }
            move_lines.append((0, 0, credit_move_vals))
            debit_move_vals = {
                'ref': id.name,
                'name': id.name,
                'date': id.date,
                'account_id': account.id,
                'branch_id': id.branch_id.id if id.branch_id else False,
                'debit': id.credit,
                'credit': 0.0,
                'object_cost_id': id.object_cost_id.id
            }
            move_lines.append((0, 0, debit_move_vals))
            move_vals = {
                'ref': id.name,
                'date': id.date,
                'journal_id': journal_id.id,
                'branch_id': id.branch_id.id if id.branch_id else False,
                'company_id': self.company_id.id,
                'line_ids': move_lines,
            }
            move_id = self.env['account.move'].create(move_vals)
            move_id.company_id = id.company_id.id,
            id.move_id = move_id
            move_id.post()
            sql = """
                UPDATE account_move_line a
                SET x_update_account_balance = 't', x_value_backup = abs(balance), debit = 0, credit = 0, balance = 0, amount_currency = 0, 
                amount_residual = 0
                where account_id = %d and move_id = %d;
            """
            self._cr.execute(sql % (account.id, move_id.id))
        return id

    def write(self, vals):
        if not self.company_id.x_date_opening_balance:
            raise except_orm(_('Thông báo'),
                             _('Bạn chưa cấu hình ngày chốt số dư!'))
        if not self.company_id.x_account_opening_balance_id:
            raise except_orm(_('Thông báo'),
                             _('Bạn chưa cấu hình tài khoản chốt số dư trong công ty!'))
        if 'debit' in vals.keys():
            sql = """
                update account_move_line set debit = %d where move_id = %d;
                update account_move_line set balance = %d where move_id = %d;
                update account_move_line set credit = 0 where move_id = %d;
            """
            self._cr.execute(sql % (vals.get('debit'), self.move_id.id, vals.get('debit'),
                                    self.move_id.id, self.move_id.id))
        if 'credit' in vals.keys():
            sql = """
                update account_move_line set credit = %d where move_id = %d;
                update account_move_line set balance = %d where move_id = %d;
                update account_move_line set debit = 0 where move_id = %d;
            """
            self._cr.execute(sql % (vals.get('credit'), self.move_id.id, -vals.get('credit'),
                                    self.move_id.id, self.move_id.id))
        if 'object_cost_id' in vals.keys():
            sql = """
                    update account_move_line set object_cost_id = %d where move_id = %d;
                """
            self._cr.execute(sql % (vals.get('object_cost_id'), self.move_id.id))
        return super(AccountBalanceObjectCost, self).write(vals)

    def unlink(self):
        for line in self:
            if line.move_id:
                move_id = line.move_id.with_context(force_delete=True)
                move_id.button_cancel()
                move_id.unlink()
        return super(AccountBalanceObjectCost, self).unlink()
