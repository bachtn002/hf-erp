# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_close_invoice_purchase(self):
        self.ensure_one()
        invoice_status = 'invoiced'
        self._update_purchase_order(invoice_status)
        journal_id = self.env['account.journal'].search([('code', '=', 'KHAC')], limit=1)
        for line in self.order_line:
            move_lines = []
            if line.qty_invoiced > line.qty_received:
                if not line.product_id.product_tmpl_id.categ_id.x_account_difference_purchase_id:
                    raise UserError(_('You have not configured the account for the difference in goods import'))
                qty = line.qty_received - line.qty_invoiced
                debit_move = {
                    'account_id': line.product_id.product_tmpl_id.categ_id.x_account_difference_purchase_id.id,
                    'name': line.product_id.product_tmpl_id.name,
                    'partner_id': self.partner_id.id,
                    'product_id': line.product_id.id,
                    'quantity': qty,
                    'debit': 0,
                    'credit': 0,
                    'x_type_transfer': 'in'
                }
                move_lines.append((0, 0, debit_move))
                credit_move = {
                    'account_id': line.product_id.product_tmpl_id.categ_id.property_stock_valuation_account_id.id,
                    'name': line.product_id.product_tmpl_id.name,
                    'product_id': line.product_id.id,
                    'partner_id': self.partner_id.id,
                    'quantity': qty,
                    'debit': 0,
                    'credit': 0,
                    'x_type_transfer': 'in'
                }
                move_lines.append((0, 0, credit_move))
                account_move = self.env['account.move'].create({
                    'ref': self.name,
                    'date': self.date,
                    'journal_id': journal_id.id,
                    'x_purchase_order_id': self.id,
                    'move_type': 'entry',
                    'line_ids': move_lines,
                })
                account_move.post()
            elif line.qty_invoiced < line.qty_received:
                if not line.product_id.product_tmpl_id.categ_id.x_account_difference_purchase_id:
                    raise UserError(_('You have not configured the account for the difference in goods import'))
                qty = line.qty_received - line.qty_invoiced
                debit_move = {
                    'account_id': line.product_id.product_tmpl_id.categ_id.property_stock_valuation_account_id.id,
                    'name': line.product_id.product_tmpl_id.name,
                    'product_id': line.product_id.id,
                    'partner_id': self.partner_id.id,
                    'quantity': qty,
                    'debit': 0,
                    'credit': 0,
                    'x_type_transfer': 'in'
                }
                move_lines.append((0, 0, debit_move))
                credit_move = {
                    'account_id': line.product_id.product_tmpl_id.categ_id.x_account_difference_purchase_id.id,
                    'name': line.product_id.product_tmpl_id.name,
                    'product_id': line.product_id.id,
                    'partner_id': self.partner_id.id,
                    'quantity': qty,
                    'debit': 0,
                    'credit': 0,
                    'x_type_transfer': 'in'
                }
                move_lines.append((0, 0, credit_move))
                account_move = self.env['account.move'].create({
                    'ref': self.name,
                    'date': self.date,
                    'journal_id': journal_id.id,
                    'x_purchase_order_id': self.id,
                    'move_type': 'entry',
                    'line_ids': move_lines,
                })
                account_move.post()

    def _update_purchase_order(self, invoice_status):
        try:
            query = """
                        UPDATE purchase_order SET invoice_status = '%s'
                        WHERE id = %d
                    """
            self._cr.execute(query % (invoice_status, self.id))
            self._cr.commit()
        except Exception as e:
            raise ValidationError(e)