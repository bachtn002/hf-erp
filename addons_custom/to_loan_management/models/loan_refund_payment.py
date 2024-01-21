from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_is_zero


class LoanRefundPayment(models.Model):
    _name = 'loan.refund.payment'
    _inherit = 'abstract.loan.payment'
    _description = 'Loan Refund Payment'

    matched_amount = fields.Monetary(compute='_compute_matched_amount', store=True)
    loan_lend_refund_payment_match_ids = fields.One2many('loan.lend.refund.payment.match', 'payment_id')
    loan_borrow_refund_payment_match_ids = fields.One2many('loan.borrow.refund.payment.match', 'payment_id')
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True, store=True)

    @api.depends('payment_type', 'loan_lend_refund_payment_match_ids.matched_amount', 'loan_borrow_refund_payment_match_ids.matched_amount')
    def _compute_matched_amount(self):
        for r in self:
            matched_amount = 0.0
            refund_payment_match_ids = self._get_refund_payment_matches()
            if refund_payment_match_ids:
                matched_amount = sum(refund_payment_match_ids.mapped('matched_amount'))
            r.matched_amount = matched_amount

    def _get_refund_payment_matches(self):
        refund_payment_match_ids = False
        if self.payment_type == 'inbound':
            refund_payment_match_ids = self.loan_lend_refund_payment_match_ids
        elif self.payment_type == 'outbound':
            refund_payment_match_ids = self.loan_borrow_refund_payment_match_ids
        return refund_payment_match_ids

    def _get_refunds(self):
        refund_ids = False
        refund_payment_match_ids = self._get_refund_payment_matches()
        if refund_payment_match_ids:
            refund_ids = refund_payment_match_ids.mapped('refund_id')
        return refund_ids

    def _get_loan_account(self):
        return self._get_refunds()[0].account_id

    def _prepare_acc_move_lines_data(self):
        data = super(LoanRefundPayment, self)._prepare_acc_move_lines_data()
        amount, amount_currency, diff_currency, possitive_amount = self._prepare_amounts()
        ctx = dict(self._context, lang=self.partner_id.lang)
        # split loan line into multiple lines corresponding to the payment matches
        new_lines = []
        payment_ref = []
        debit_sum = 0.0
        credit_sum = 0.0
        for payment_match in self._get_refund_payment_matches():
            if float_is_zero(amount, precision_rounding=self.company_id.currency_id.rounding):
                continue
            # take a part of the amount that is not greater than the to_pay_amount
            refund_id = payment_match.refund_id
            if diff_currency:
                matched_amount = self.currency_id.with_context(ctx)._convert(payment_match.matched_amount, self.company_id.currency_id, self.company_id, self.payment_date)
                refund_amt = matched_amount if float_compare(amount, matched_amount, precision_rounding=self.company_id.currency_id.rounding) == 1 else amount
                refund_amt_currency = payment_match.matched_amount if float_compare(amount_currency, payment_match.matched_amount, precision_rounding=self.currency_id.rounding) == 1 else amount_currency
            else:
                refund_amt = payment_match.matched_amount if float_compare(amount, payment_match.matched_amount, precision_rounding=self.company_id.currency_id.rounding) == 1 else amount
                refund_amt_currency = 0.0
            amount -= refund_amt
            amount_currency -= refund_amt_currency

            debit = -1.0 * refund_amt if not possitive_amount else 0.0
            debit_sum += debit
            credit = refund_amt if possitive_amount else 0.0
            credit_sum += credit

            new_line = data[0][2].copy()
            update_data = {
                'date_maturity': refund_id.date_maturity,
                'debit': debit,
                'credit': credit,
                'ref': _("Loan Refund Payment %s") % (refund_id.name,),
                'name': refund_id.name,
                }
            if diff_currency:
                if float_compare(credit, 0.0, precision_rounding=self.company_id.currency_id.rounding) == 1:
                    update_data['amount_currency'] = -1.0 * abs(refund_amt_currency)
                elif float_compare(debit, 0.0, precision_rounding=self.company_id.currency_id.rounding) == 1:
                    update_data['amount_currency'] = abs(refund_amt_currency)
            new_line.update(update_data)
            new_lines.append((0, 0, new_line))
            payment_ref.append(payment_match.disbursement_id.name)

        data[1][2]['name'] = _("Loan Refund Payment")
        # replace the existing loan line with the new ones
        if new_lines:
            del data[0]
            # correct the last line to ensure credit sum == debit sum in the journal entry
            if float_compare(debit_sum, 0.0, precision_rounding=self.company_id.currency_id.rounding) == 1:
                if float_compare(debit_sum, data[0][2]['credit'], precision_rounding=self.company_id.currency_id.rounding):
                    new_lines[-1][2]['debit'] -= debit_sum - data[0][2]['credit']
            elif float_compare(credit_sum, 0.0, precision_rounding=self.company_id.currency_id.rounding) == 1:
                if float_compare(credit_sum, data[0][2]['debit'], precision_rounding=self.company_id.currency_id.rounding):
                    new_lines[-1][2]['credit'] -= credit_sum - data[0][2]['debit']
            data = new_lines + data

        return data

    def create_account_move(self):
        if float_compare(self.amount, self.matched_amount, precision_rounding=self.currency_id.rounding) == 1:
            raise ValidationError(_("Payments that are not fully matched with refunds may not be able to get posted."))
        refund_ids = self._get_refunds()
        if not refund_ids:
            raise (_("No refund found for payment journal entry creation. Please try to match the payment with refund(s) first."))
        return self.env['account.move'].create(self._parepare_account_move_data())

    def match_payments(self, refund_ids):
        refund_ids.match_payments(self)

    @api.model
    def _get_not_match_err_msg(self):
        return _("Payments that are not fully matched with loan refund(s) may not be able to get posted into accounting system."
                 " You may need to register the payment from Principal Refund menu entry...")

    def reconcile_disbusement(self):
        """
        Reconcile refund move lines with their corresponding disbursements' move lines
        """
        for r in self:
            if not r.move_id:
                continue
            move_line_ids = r.move_id.line_ids.filtered(lambda line: line.account_id.reconcile and not line.full_reconcile_id)
            if not move_line_ids:
                continue
            refund_ids = r._get_refunds()
            if refund_ids:
                move_line_ids += refund_ids.mapped('disbursement_id.move_ids.line_ids').filtered(lambda line: line.account_id.reconcile and not line.full_reconcile_id)
                # can do partially reconciled
                # move_line_ids.auto_reconcile_lines()
                # move_line_ids.move_id.js_assign_outstanding_line(move_line_ids.id)

    def action_post(self):
        for r in self:
            refund_ids = r._get_refunds()
            if refund_ids:
                paid_refund_ids = refund_ids.filtered(lambda d: float_compare(d.paid_amount, d.amount, d.currency_id.rounding) == 0)
                if paid_refund_ids:
                    paid_refund_ids.with_context(full_payment_date=r.payment_date).action_paid()
        super(LoanRefundPayment, self).action_post()
        # Reconcile refund move lines with disbursement move lines
        self.reconcile_disbusement()

    def action_cancel(self):
        super(LoanRefundPayment, self).action_cancel()
        for line in self.mapped('loan_borrow_refund_payment_match_ids'):
            if line.refund_id.disbursement_id.state == 'refunded':
                line.refund_id.disbursement_id.state = 'paid'
        self.mapped('loan_lend_refund_payment_match_ids').unlink()
        self.mapped('loan_borrow_refund_payment_match_ids').unlink()

