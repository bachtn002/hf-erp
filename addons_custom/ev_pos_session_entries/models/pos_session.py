# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosSesssionEntries(models.Model):
    _inherit = 'pos.session'

    x_update_entries = fields.Boolean('Update Entries', default=False)

    def action_pos_session_update_entries(self):
        for record in self:
            if record.state != 'closed':
                return
            if record.move_id.journal_id.type == 'sale':
                account_receivable_id = self.env['ir.property']._get('property_account_receivable_id', 'res.partner')
                total_debit = 0
                total_credit = 0
                total_receivable = 0
                for line in record.move_id.line_ids:
                    if line.account_id.id == account_receivable_id.id and line.debit > 0:
                        total_receivable += line.debit
                    if line.credit > 0:
                        total_credit += line.credit
                    if line.debit > 0:
                        total_debit += line.debit
                    if line.account_id.id == account_receivable_id.id:
                        line.write({'contra_account_id': False})
                        continue
                    line.write({'contra_account_id': account_receivable_id.id})

                if record.x_update_entries:
                    break
                MoveLine = self.env['account.move.line']
                MoveLine.create([self._create_account_move_line_credit_entries(account_receivable_id.id, record.move_id.id,
                                                                  'Receivables from customers', total_credit - total_receivable)] +
                                [self._create_account_move_line_debit_entries(account_receivable_id.id,
                                                                             record.move_id.id,
                                                                             'Receivables from customers',
                                                                             total_debit - total_receivable)]
                                )
                record.x_update_entries = True


    @api.model
    def _action_pos_session_update_entries(self):
        records = self.search([
            ('state', '=', 'closed'),
            ('x_update_entries','=', True)
        ])
        records.action_pos_session_update_entries()





    def _create_account_move_line_debit_entries(self, account_id, move_id, name, amount_converted):
        move_line = {
            'account_id': account_id,
            'move_id': move_id,
            'name': name,
            'debit': amount_converted if amount_converted > 0.0 else 0.0,
            'credit': -amount_converted if amount_converted < 0.0 else 0.0,
        }
        return move_line

    def _create_account_move_line_credit_entries(self, account_id, move_id, name, amount_converted):
        move_line = {
            'account_id': account_id,
            'move_id': move_id,
            'name': name,
            'debit': -amount_converted if amount_converted < 0.0 else 0.0,
            'credit': amount_converted if amount_converted > 0.0 else 0.0,
        }
        return move_line



