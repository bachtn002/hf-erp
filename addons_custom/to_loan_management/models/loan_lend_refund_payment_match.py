from odoo import models, fields


class LoanLendRefundPaymentMatch(models.Model):
    _name = 'loan.lend.refund.payment.match'
    _description = 'Loan Lend Refund Payment Match'
    _inherit = 'abstract.refund.payment.match'

    refund_id = fields.Many2one('loan.lend.refund.line', string='Refund', ondelete='cascade', index=True)
    disbursement_id = fields.Many2one(related='refund_id.disbursement_id', readonly=True)
    order_id = fields.Many2one(related='refund_id.order_id', store=True, index=True)

    def get_payment_matches_field(self):
        """
        Return the name of the field `loan_lend_refund_payment_match_ids` of the model `loan.disbursement.payment`
        """
        return 'loan_lend_refund_payment_match_ids'
