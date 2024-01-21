from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class LoanBorrowingOrder(models.Model):
    _name = 'loan.borrowing.order'
    _description = 'Borrowing Loan Contract'
    _inherit = 'abstract.loan.order'

    
    disbursement_line_ids = fields.One2many('loan.borrow.disbursement', 'order_id',
                                                 string='Disbursements', copy=False,
                                                 states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})

    refund_line_ids = fields.One2many('loan.borrow.refund.line', 'order_id',
                                                     string='Principal Refunds', copy=False,
                                                     states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})
    refund_lines_count = fields.Integer(compute='_compute_refund_lines_count', copy=False)
    interest_line_ids = fields.One2many('loan.borrow.interest.line', 'order_id',
                                                     string='Interests', copy=False,
                                                     states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})
    interest_lines_count = fields.Integer(string='Interests Count', compute='_compute_interest_lines_count', copy=False)

    invoice_ids = fields.Many2many('account.move', 'borrowing_order_invoice_rel', 'order_id', 'invoice_id',
                                   string='Invoices', copy=False)

    disbursement_payment_match_ids = fields.One2many('loan.borrow.disbursement.payment.match', 'order_id', string='Disbursements & Payments Matches', copy=False)
    refund_payment_match_ids = fields.One2many('loan.borrow.refund.payment.match', 'order_id', string='Refunds & Payments Matches', copy=False)

    account_id = fields.Many2one(help="The Loan Account that holds the borrowing loan for this contract", default=lambda self: self.env.company.loan_borrowing_account_id)
    journal_id = fields.Many2one(domain=lambda self: self._get_journal_domain(), default=lambda self: self.env.company.loan_borrowing_journal_id,
                                 help="The accounting journal that will be used when invoicing interest of this loan contract."
                                 " It should be a purchase journal with expense accounts set")

    tax_ids = fields.Many2many(domain=[('type_tax_use', '=', 'purchase')])
    invoice_state = fields.Selection([
        ('nothing_to_invoice', 'Nothing To Bill'),
        ('to_invoice', 'To Bill'),
        ('fully_invoiced', 'Fully Billed')], string='Billing Status')
    payment_term_id = fields.Many2one(help="The payment term that applies to the Loan Interest Bills")

    disbursement_dt_ids = fields.One2many('loan.borrow.disbursement.dt','order_id',string='Detail')



    @api.depends('disbursement_start_date','loan_duration')
    def _compute_date_end(self):
        for r in self:
            if r.disbursement_start_date and r.loan_duration:
                r.date_end = r.disbursement_start_date + relativedelta(months=+r.loan_duration)
                for item in r.disbursement_line_ids:
                    item.date_start = r.disbursement_start_date
                    item.loan_duration = r.loan_duration

    def _get_journal_domain(self):
        return [('type', '=', 'purchase')]

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.tax_ids = self.product_id.supplier_taxes_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('borrow.order') or '/'
        return super(LoanBorrowingOrder, self).create(vals_list)

    def _get_disbursement_model(self):
        return 'loan.borrow.disbursement'

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
        return 'to_loan_management.loan_borrowing_refund_line_action'

    def _get_refund_line_form_view_xml_id(self):
        return 'to_loan_management.loan_borrowing_refund_line_form_view'

    def _get_interest_line_action_xml_id(self):
        return 'to_loan_management.loan_borrowing_interest_line_action'

    def _get_interest_line_form_view_xml_id(self):
        return 'to_loan_management.loan_borrowing_interest_line_form_view'

    def _get_disbursement_payment_action_xml_id(self):
        return 'to_loan_management.action_loan_borrow_disbursement_payment_wizard'

    def _get_invoicing_wizard_action_xml_id(self):
        return 'to_loan_management.borrow_interest_invoicing_wizard_action'
