from odoo import models, fields


class LoanBorrowRefundLine(models.Model):
    _name = 'loan.borrow.refund.line'
    _inherit = 'abstract.loan.refund'
    _description = 'Loan Borrow Refund Line'

    disbursement_id = fields.Many2one('loan.borrow.disbursement', string='Disbursement', required=True, ondelete='cascade', index=True,
                                      readonly=True, states={'draft': [('readonly', False)]})
    order_id = fields.Many2one(related='disbursement_id.order_id', store=True, index=True, readonly=True)
    currency_id = fields.Many2one(related='disbursement_id.currency_id', store=True, readonly=True)
    payment_match_ids = fields.One2many('loan.borrow.refund.payment.match', 'refund_id', string='Payment Matches', readonly=True)
    payment_ids = fields.Many2many('loan.refund.payment', 'refund_payment_borrow_refund_line_rel', 'refund_id', 'payment_id',
                                   string='Payments', compute='_compute_payment_ids', store=True)
    move_ids = fields.Many2many('account.move', 'acc_move_borrow_refund_line_rel', 'refund_id', 'move_id',
                                string="Journal Entries", compute='_compute_move_ids', store=True)

    partner_id = fields.Many2one(related='order_id.partner_id', store=True, readonly=True)
    company_id = fields.Many2one(related='order_id.company_id', store=True, readonly=True)
    journal_id = fields.Many2one(related='order_id.journal_id', readonly=True)
    account_id = fields.Many2one(related='order_id.account_id', readonly=True)

    def _get_sequence(self):
        return self.env['ir.sequence'].next_by_code('loan.borrowing.refund') or '/'

    def _get_refund_payment_action_xml_id(self):
        return 'to_loan_management.action_loan_borrow_refund_payment_wizard'

    def _get_payment_match_model(self):
        return 'loan.borrow.refund.payment.match'

    def action_cancel(self):
        if self._name == 'loan.borrow.refund.line':
            for rec in self:
                for payment in rec.payment_ids:
                    payment.action_cancel()
                rec.disbursement_id.state = 'paid'
        res = super(LoanBorrowRefundLine, self).action_cancel()
        return res