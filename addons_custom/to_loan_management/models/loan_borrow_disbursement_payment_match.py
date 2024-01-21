from odoo import models, fields, _


class LoanBorrowDisbursementPaymentMatch(models.Model):
    _name = 'loan.borrow.disbursement.payment.match'
    _inherit = 'abstract.disbursement.payment.match'
    _description = 'Loan Borrow Disbursement Payment Match'

    disbursement_id = fields.Many2one('loan.borrow.disbursement', string='Disbursement', ondelete='cascade', index=True, required=True)
    order_id = fields.Many2one(related='disbursement_id.order_id', store=True, index=True, readonly=True)

    def get_payment_matches_field(self):
        """
        Return the name of the field `loan_borrow_disbursement_payment_match_ids` of the model `loan.disbursement.payment`
        """
        return 'loan_borrow_disbursement_payment_match_ids'

    def action_show_popup_choose_word_tpl(self):
        self.ensure_one()
        return {
            'name': _('Print Template'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'template.bank.wizard',
            'no_destroy': False,
            'target': 'new',
            'view_id': self.env.ref(
                'to_loan_management.word_template_wizard_form') and self.env.ref(
                'to_loan_management.word_template_wizard_form').id or False,
            'context': {'default_disbursement_payment_match_id': self.id,
                        'default_borrow_disbursement_id': self.disbursement_id.id},
        }
