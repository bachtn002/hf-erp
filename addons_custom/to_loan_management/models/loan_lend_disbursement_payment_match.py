from odoo import models, fields


class LoanLendDisbursementPaymentMatch(models.Model):
    _name = 'loan.lend.disbursement.payment.match'
    _description = 'Lending Loan Disbursement Payment Match'
    _inherit = 'abstract.disbursement.payment.match'

    disbursement_id = fields.Many2one('loan.lend.disbursement', string='Disbursement', ondelete='cascade', index=True)
    order_id = fields.Many2one(related='disbursement_id.order_id', store=True, index=True)

    def get_payment_matches_field(self):
        """
        Return the name of the field `loan_lend_disbursement_payment_match_ids` of the model `loan.disbursement.payment`
        """
        return 'loan_lend_disbursement_payment_match_ids'
