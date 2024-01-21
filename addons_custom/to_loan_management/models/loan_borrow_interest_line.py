from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LoanBorrowInterestLine(models.Model):
    _name = 'loan.borrow.interest.line'
    _inherit = 'abstract.loan.interest'
    _description = 'Loan Borrow Interest Line'

    disbursement_id = fields.Many2one('loan.borrow.disbursement', string='Disbursement', required=True, ondelete='cascade', index=True,
                                      readonly=True, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one(related='disbursement_id.company_id', store=True, readonly=True)
    disbursement_state = fields.Selection(related='disbursement_id.state', string='Disbursement Status', store=True, index=True)
    order_id = fields.Many2one(related='disbursement_id.order_id', store=True, index=True, readonly=True)
    partner_id = fields.Many2one(related='disbursement_id.partner_id', store=True, index=True, readonly=True)
    currency_id = fields.Many2one(related='disbursement_id.currency_id', store=True, readonly=True)
    invoice_line_ids = fields.One2many('account.move.line', 'loan_borrow_interest_line_id', string='Bill Lines', readonly=True)
    invoice_ids = fields.Many2many('account.move', 'loan_borrow_interest_line_invoice_rel', 'loan_borrow_interest_line_id', 'invoice_id',
                                   string='Invoices', compute='_compute_invoices', store=True)
    invoiced_amount = fields.Monetary(string='Billed Amount', compute='_compute_invoiced_amount', store=True)
    to_invoice_amount = fields.Monetary(string='To Bill Amount', compute='_compute_to_invoice_amount', store=True)
    fully_invoiced = fields.Boolean(string="Fully Billed", help="Technical field to indicate if the loan interest has been billed fully")

    @api.onchange('disbursement_id')
    def _onchange_disbursement(self):
        if self.disbursement_id:
            self.date_from = self.disbursement_id.last_interest_date_to

    def _get_sequence(self):
        return self.env['ir.sequence'].next_by_code('loan.borrow.interest') or '/'

    def _get_interest_account(self):
        account = self.order_id.product_id.product_tmpl_id._get_product_accounts()['expense']
        if not account:
            raise ValidationError(_('Please define expense account for this product: "%s" (id:%d) - or for its category: "%s".')
                                  % (self.order_id.product_id.display_name, self.order_id.product_id.id, self.order_id.product_id.categ_id.name))

        fpos = self._get_financial_fiscal_position()
        if fpos:
            account = fpos.map_account(account)
        return account

    def _get_invoicing_wizard_action_xml_id(self):
        return 'to_loan_management.borrow_interest_invoicing_wizard_action'

    def _get_invoice_type(self):
        return 'in_invoice'

    def _get_invoice_action_xml_id(self):
        return 'account.action_move_in_invoice_type'

    def _get_partner_account(self, partner_id):
        return partner_id.property_account_payable_id
