from odoo import models, fields


class LoanBorrowRefundPaymentMatch(models.Model):
    _name = 'loan.borrow.refund.payment.match'
    _inherit = 'abstract.refund.payment.match'
    _description = 'Loan Borrow Refund Payment Match'

    refund_id = fields.Many2one('loan.borrow.refund.line', string='Refund', ondelete='cascade', index=True, required=True)
    disbursement_id = fields.Many2one(related='refund_id.disbursement_id', readonly=True)
    order_id = fields.Many2one(related='refund_id.order_id', store=True, index=True, readonly=True)

    def get_payment_matches_field(self):
        """
        Return the name of the field `loan_borrow_disbursement_payment_match_ids` of the model `loan.disbursement.payment`
        """
        return 'loan_borrow_refund_payment_match_ids'

    def action_print_uy_nhiem_chi(self):
        self.ensure_one()
        return {
            'name': ('Print UNC'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.choose.word.template',
            'no_destroy': False,
            'target': 'new',
            'view_id': self.env.ref(
                'to_loan_management.wizard_choose_word_template_view_form') and self.env.ref(
                'to_loan_management.wizard_choose_word_template_view_form').id or False,
            'context': {'default_refund_payment_id': self.id},
        }
