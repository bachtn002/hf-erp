from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class AbstractLoanRefundPaymentWizard(models.AbstractModel):
    _name = 'abstract.loan.refund.payment.wizard'
    _inherit = 'abstract.loan.payment'
    _description = 'Loan Refund Payment Wizard Abstract'

    company_id = fields.Many2one(compute='_compute_company', store=True)

    @api.constrains('refund_ids')
    def _check_refund_ids(self):
        for r in self:
            company_id = r.refund_ids.mapped('company_id')
            if len(company_id) > 1:
                raise ValidationError(_("You cannot make payment for refunds to multiple companies at once"))
            if self.company_id and self.company_id.id != company_id.id:
                raise ValidationError(_("The payment is for the company '%s' while the matched refund(s) belongs to another company (%s)")
                                      % (self.company_id.name, company_id.name))
            partner_id = r.refund_ids.mapped('partner_id')
            if len(partner_id) > 1:
                raise ValidationError(_("You cannot make payment for the refunds that concerning multiple partners"))
            currency_id = r.refund_ids.mapped('currency_id')
            if len(currency_id) > 1:
                raise ValidationError(_("You cannot make payment for the refunds that are in different currencies at once"))

    @api.constrains('refund_ids', 'amount')
    def _check_amount_vs_refunds(self):
        for r in self:
            if not r.refund_ids:
                continue

            remaining_amt = r._calculate_remaining_amount()
            if float_compare(r.amount, remaining_amt, precision_rounding=r.currency_id.rounding) == 1:
                raise ValidationError(_("Payment Amount should not be greater than the total remaining amount of the selected refund(s)"))

    @api.depends('refund_ids.company_id')
    def _compute_company(self):
        for r in self:
            r.company_id = r.refund_ids[0].company_id if r.refund_ids else False

    @api.model
    def _get_default_refunds(self):
        active_ids = self.env.context.get('active_ids', [])
        return self.refund_ids.search([('id', 'in', active_ids)])

    def _calculate_remaining_amount(self):
        remaining_amt = 0.0
        if self.refund_ids:
            remaining_amt = sum(self.refund_ids.mapped('to_pay_amount'))
        return remaining_amt

    def _onchange_refund_ids(self):
        res = {}
        self.amount = self._calculate_remaining_amount()
        self.communication = ", ".join(self.refund_ids.mapped('name'))
        self.partner_id = self.refund_ids[0].partner_id if self.refund_ids else False
        currency_ids = self.refund_ids.mapped('currency_id')
        journal_id_domain = [('type', 'in', ('bank', 'cash'))]
        if currency_ids:
            if any(currency_id.id == self.company_id.currency_id.id for currency_id in currency_ids):
                journal_id_domain += ['|', ('currency_id', '=', False), ('currency_id', 'in', currency_ids.ids)]
            else:
                journal_id_domain += [('currency_id', 'in', currency_ids.ids)]
        res['domain'] = {'journal_id':journal_id_domain}
        return res

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.refund_ids = self.refund_ids.search([('partner_id', '=', self.partner_id.id), ('state', '=', 'confirmed')])

    def action_payment_create_and_match(self):
        self.ensure_one()
        payment_id = self.env['loan.refund.payment'].create(self._prepare_payment_data())
        self.refund_ids.match_payments(payment_id)
        if payment_id.state == 'matched':
            payment_id.action_post()

    @api.onchange('amount')
    def _onchange_amount(self):
        # if the amount is greater than the existing refunds' to_pay_amount, load more refunds from the same disbursement
        disbursement_ids = self.refund_ids.mapped('disbursement_id')
        while float_compare(self.amount, sum(self.mapped('refund_ids.to_pay_amount')), precision_rounding=self.currency_id.rounding) == 1:
            remain_refund_line_ids = disbursement_ids.mapped('refund_line_ids').filtered(lambda l: l.id not in self.refund_ids.ids and l.state == 'confirmed')
            if not remain_refund_line_ids:
                break
            self.refund_ids += remain_refund_line_ids[0]

        # if the amount is still greater than the existing refunds' to_pay_amount, load more refunds from the same order
        order_ids = self.refund_ids.mapped('order_id')
        while float_compare(self.amount, sum(self.mapped('refund_ids.to_pay_amount')), precision_rounding=self.currency_id.rounding) == 1:
            remain_refund_line_ids = order_ids.mapped('refund_line_ids').filtered(lambda l: l.id not in self.refund_ids.ids and l.state == 'confirmed')
            if not remain_refund_line_ids:
                break
            self.refund_ids += remain_refund_line_ids[0]


class LoanBorrowRefundPaymentWizard(models.TransientModel):
    _name = 'loan.borrow.refund.payment.wizard'
    _inherit = 'abstract.loan.refund.payment.wizard'
    _description = 'Loan Borrow Refund Payment Wizard'

    refund_ids = fields.Many2many('loan.borrow.refund.line', 'loan_borrow_refund_payment_wizard_rel', 'wizard_id', 'refund_id',
                                        string='Refunds',
                                        default=lambda self: self._get_default_refunds())

    @api.onchange('refund_ids')
    def _onchange_refund_ids(self):
        super(LoanBorrowRefundPaymentWizard, self)._onchange_refund_ids()


class LoanLendRefundPaymentWizard(models.TransientModel):
    _name = 'loan.lend.refund.payment.wizard'
    _inherit = 'abstract.loan.refund.payment.wizard'
    _description = 'Loan Lend Refund Payment Wizard'

    refund_ids = fields.Many2many('loan.lend.refund.line', 'loan_lend_refund_payment_wizard_rel', 'wizard_id', 'refund_id',
                                        string='Refunds',
                                        default=lambda self: self._get_default_refunds())

    @api.onchange('refund_ids')
    def _onchange_refund_ids(self):
        super(LoanLendRefundPaymentWizard, self)._onchange_refund_ids()

