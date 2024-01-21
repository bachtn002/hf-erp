from odoo import models, fields, api


class LendingLoanOrder(models.Model):
    _name = 'loan.lending.order'
    _description = 'Lending Loan Contract'
    _inherit = 'abstract.loan.order'

    disbursement_line_ids = fields.One2many('loan.lend.disbursement', 'order_id',
                                                 string='Disbursement Plan lines', copy=False,
                                                 states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})

    refund_line_ids = fields.One2many('loan.lend.refund.line', 'order_id',
                                                     string='Principal Refunds', copy=False,
                                                     states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})
    refund_lines_count = fields.Integer(string='Disbursements Count', compute='_compute_refund_lines_count', copy=False)
    interest_line_ids = fields.One2many('loan.lend.interest.line', 'order_id',
                                                     string='Interests', copy=False,
                                                     states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})
    interest_lines_count = fields.Integer(string='Interests Count', compute='_compute_interest_lines_count')

    invoice_ids = fields.Many2many('account.move', 'lending_order_invoice_rel', 'order_id', 'invoice_id',
                                   string='Invoices', copy=False)

    disbursement_payment_match_ids = fields.One2many('loan.lend.disbursement.payment.match', 'order_id', string='Disbursements & Payments Matches')
    refund_payment_match_ids = fields.One2many('loan.lend.refund.payment.match', 'order_id', string='Refunds & Payments Matches', copy=False)

    account_id = fields.Many2one(help="The Loan Account that holds the lending loan for this contract", default=lambda self: self.env.company.loan_lending_account_id)
    journal_id = fields.Many2one(domain=lambda self: self._get_journal_domain(), default=lambda self: self.env.company.loan_lending_journal_id,
                                 help="The accounting journal that will be used when invoicing interest of this loan contract."
                                 " It should be a sale journal with income accounts set")
    tax_ids = fields.Many2many(domain=[('type_tax_use', '=', 'sale')])
    payment_term_id = fields.Many2one(help="The payment term that applies to the Loan Interest Invoices")


    def _get_journal_domain(self):
        return [('type', '=', 'sale')]

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.tax_ids = self.product_id.taxes_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('lend.order') or '/'
        return super(LendingLoanOrder, self).create(vals_list)

    def _get_disbursement_model(self):
        return 'loan.lend.disbursement'

    def _get_invoice_action_xml_id(self):
        return 'account.action_move_in_invoice_type'

    @api.depends('interest_line_ids')
    def _compute_interest_lines_count(self):
        for r in self:
            r.interest_lines_count = len(r.interest_line_ids)

    @api.depends('refund_line_ids')
    def _compute_refund_lines_count(self):
        for r in self:
            r.refund_lines_count = len(r.refund_line_ids)

    def _get_refund_line_action_xml_id(self):
        return 'to_loan_management.loan_lending_refund_line_action'

    def _get_refund_line_form_view_xml_id(self):
        return 'to_loan_management.loan_lending_refund_line_form_view'

    def _get_interest_line_action_xml_id(self):
        return 'to_loan_management.loan_lending_interest_line_action'

    def _get_interest_line_form_view_xml_id(self):
        return 'to_loan_management.loan_lending_interest_line_form_view'

    def _get_disbursement_payment_action_xml_id(self):
        return 'to_loan_management.action_loan_lend_disbursement_payment_wizard'

    def _get_invoicing_wizard_action_xml_id(self):
        return 'to_loan_management.lend_interest_invoicing_wizard_action'
