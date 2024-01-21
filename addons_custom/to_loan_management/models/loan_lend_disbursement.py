from odoo import models, fields


class LoanLendDisbursement(models.Model):
    _name = 'loan.lend.disbursement'
    _description = 'Disbursement Plan Line'
    _inherit = 'abstract.loan.disbursement'

    order_id = fields.Many2one('loan.lending.order', string='Contract', required=True, readonly=True, states={'draft': [('readonly', False)]},
                               help="The Lending Loan contract that the disbursement follows")
    partner_id = fields.Many2one(related='order_id.partner_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='order_id.currency_id', store=True, readonly=True)
    company_id = fields.Many2one(related='order_id.company_id', store=True, readonly=True)
    journal_id = fields.Many2one(related='order_id.journal_id', readonly=True)
    account_id = fields.Many2one(related='order_id.account_id', readonly=True)

    refund_line_ids = fields.One2many('loan.lend.refund.line', 'disbursement_id',
                                  string='Refunds',
                                  help="The principal refund that schedules refund for this disbursement")
    interest_line_ids = fields.One2many('loan.lend.interest.line', 'disbursement_id', string='Interests',
                                        help="The scheduled interests concerning to this disbursement")
    payment_match_ids = fields.One2many('loan.lend.disbursement.payment.match', 'disbursement_id', string='Payment Matches', readonly=True)

    payment_ids = fields.Many2many('loan.disbursement.payment', 'disbursement_payment_lend_disbursement_rel', 'disbursement_id', 'payment_id',
                                   string='Payments', compute='_compute_payment_ids', store=True)
    move_ids = fields.Many2many('account.move', 'acc_move_lend_disbursement_rel', 'disbursement_id', 'move_id',
                                string="Journal Entries", compute='_compute_move_ids', store=True)

    def _get_sequence(self):
        return self.env['ir.sequence'].next_by_code('loan.lending.disbursement') or '/'

    def _get_refund_line_model(self):
        return 'loan.lend.refund.line'

    def _get_loan_interest_line_model(self):
        return 'loan.lend.interest.line'

    def _get_payment_match_model(self):
        return 'loan.lend.disbursement.payment.match'

    def _get_disbursement_payment_action_xml_id(self):
        return 'to_loan_management.action_loan_lend_disbursement_payment_wizard'
