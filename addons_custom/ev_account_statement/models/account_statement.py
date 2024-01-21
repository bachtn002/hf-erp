# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons.base.models.ir_model import field_xmlid
from datetime import datetime
from odoo.exceptions import UserError, ValidationError


class AccountStatement(models.Model):
    _name = 'account.statement'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(string="Name", required=True)
    journal_id = fields.Many2one('account.journal', strinig='Account Journal', required=True)
    date = fields.Date(string='Date Accounting', required=True, default=lambda x: datetime.today())

    account_statement_ids = fields.One2many('account.statement.line', 'account_statement_id',
                                            string='Account Statement Line')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Tag name already exists!'),
    ]

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')],
        string='state', default='draft'
    )
    count_move = fields.Float(default=0, compute='_compute_count_move')
    amount_total = fields.Float(string='Amount Total ', compute="_compute_amount_total")

    @api.depends('account_statement_ids', 'account_statement_ids.amount')
    def _compute_amount_total(self):
        for record in self:
            record.amount_total = 0
            if record.account_statement_ids:
                for line in record.account_statement_ids:
                    record.amount_total += line.amount

    @api.depends('account_statement_ids', 'account_statement_ids.account_move_id')
    def _compute_count_move(self):
        for record in self:
            record.count_move = 0
            if record.account_statement_ids:
                for rec in record.account_statement_ids:
                    if rec.account_move_id:
                        record.count_move += 1

    def action_view_move(self):
        self.ensure_one()
        move_ids = []
        for record in self:
            if record.account_statement_ids:
                for rec in record.account_statement_ids:
                    if rec.account_move_id:
                        move_ids.append(rec.account_move_id.id)
        move_ids = list(set(move_ids))
        action = self.env.ref('account.action_move_journal_line')
        result = action.sudo().read()[0]
        result['domain'] = [('id', 'in', move_ids)]
        result[
            'context'] = "{'default_move_type': 'entry', 'view_no_maturity': True, 'create': False, 'delete': False, 'edit': False}"
        return result

    @api.onchange('date')
    def onchange_date(self):
        if self.date:
            date = self.date.strftime('%d/%m/%Y')
            self.name = _('Payment of daily sales ') + str(date)

    def action_confirm(self):
        self.ensure_one()
        if self.state == 'done':
            return
        self._create_account_move()
        self.state = 'done'

    def set_to_draft(self):
        for line in self.account_statement_ids:
            line.account_move_id.button_draft()
            line.account_move_id.with_context(force_delete=True).unlink()
        self.state = 'draft'

    def _create_account_move(self):
        for line in self.account_statement_ids:
            move_lines = []
            debit_move_vals = {
                'name': line.description,
                'ref': line.code,
                'date': line.date,
                'account_id': self.journal_id.default_account_id.id,
                'debit': line.amount,
                'credit': 0.0,
                'analytic_account_id': line.account_analytic_id.id
            }
            move_lines.append((0, 0, debit_move_vals))

            # Ghi sổ thu/chi của công ty
            credit_move_vals = {
                'ref': line.code,
                'name': line.description,
                'date': line.date,
                'account_id': line.account_id.id,
                'debit': 0.0,
                'credit': line.amount,
                'analytic_account_id': line.account_analytic_id.id
            }
            move_lines.append((0, 0, credit_move_vals))
            move_vals = {
                'ref': line.code,
                'date': line.date,
                'journal_id': self.journal_id.id,
                'line_ids': move_lines,
            }
            move_id = self.env['account.move'].create(move_vals)
            move_id.post()
            line.account_move_id = move_id.id

    def download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_account_statement/static/template/importsaoke_mau.xlsx',
            "target": "_parent",
        }

    def unlink(self):
        try:
            if self.state == 'draft':
                if not self.account_statement_ids:
                    return super(AccountStatement, self).unlink()
                else:
                    for line in self.account_statement_ids:
                        line.unlink()
                    return super(AccountStatement, self).unlink()
            else:
                raise UserError(_('You can note delete'))

        except Exception as e:
            raise ValidationError(e)
