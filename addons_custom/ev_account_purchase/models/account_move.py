# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_account_move_id = fields.Many2one('account.move', 'Account Move Differrence Purchase')
    #x_purchase_order_id = fields.Many2one('purhcase.order', 'Purchase Order')

    # def action_post(self):
    #     try:
    #         super(AccountMove, self).action_post()
    #         purchase_order = self.env['purchase.order'].search([('invoice_ids', 'in', self.id)], limit=1)
    #         journal_id = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
    #         self._create_account_purchase(purchase_order, journal_id)
    #
    #         return super(AccountMove, self).action_post()
    #     except Exception as e:
    #         raise ValidationError(e)

    #
    # def button_draft(self):
    #     try:
    #         super(AccountMove, self).button_draft()
    #         # xóa bút toán chênh lệch đơn mua
    #         if self.move_type == 'in_invoice':
    #             purchase_order = self.env['purchase.order'].search([('invoice_ids', 'in', self.id)], limit=1)
    #             if purchase_order:
    #                 account_moves = self.env['account.move'].search([('x_purchase_order_id', '=', purchase_order.id)], limit=1)
    #                 if account_moves:
    #                     account_moves.button_draft()
    #                     account_moves.button_cancel()
    #                     account_moves.with_context(force_delete=True).unlink()
    #                 if purchase_order.invoice_status == 'invoiced':
    #                     invoice_status = 'to invoice'
    #                     self._update_purchase_order(purchase_order.id, invoice_status)
    #                     purchase_order.x_invoice_confirm_diff = False
    #         return super(AccountMove, self).button_draft()
    #     except Exception as e:
    #         raise ValidationError(e)

    def _update_purchase_order(self, purchase_order, invoice_status):
        try:
            query = """
                        UPDATE purchase_order SET invoice_status = '%s'
                        WHERE id = %d
                    """
            self._cr.execute(query % (invoice_status, purchase_order))
            self._cr.commit()
        except Exception as e:
            raise ValidationError(e)
