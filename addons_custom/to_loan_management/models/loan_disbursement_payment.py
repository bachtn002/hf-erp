from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_is_zero


class LoanDisbursementPayment(models.Model):
    _name = 'loan.disbursement.payment'
    _inherit = 'abstract.loan.payment'
    _description = 'Loan Disbursement Payment'

    matched_amount = fields.Monetary(compute='_compute_matched_amount', store=True)
    loan_lend_disbursement_payment_match_ids = fields.One2many('loan.lend.disbursement.payment.match', 'payment_id')
    loan_borrow_disbursement_payment_match_ids = fields.One2many('loan.borrow.disbursement.payment.match', 'payment_id')
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True, store=True)
    purchase_order_ids = fields.Many2many('purchase.order', string='Contracts')
    invoice_ids = fields.Many2many('account.move','loan_payment_acc_invoice_rel', string='Invoices')
    # description = fields.Char(string='Description')

    @api.depends('payment_type', 'loan_lend_disbursement_payment_match_ids.matched_amount', 'loan_borrow_disbursement_payment_match_ids.matched_amount')
    def _compute_matched_amount(self):
        for r in self:
            matched_amount = 0.0
            disbursement_payment_match_ids = self._get_disbursement_payment_matches()
            if disbursement_payment_match_ids:
                matched_amount = sum(disbursement_payment_match_ids.mapped('matched_amount'))
            r.matched_amount = matched_amount

    def _get_disbursement_payment_matches(self):
        disbursement_payment_match_ids = False
        if self.payment_type == 'outbound':
            disbursement_payment_match_ids = self.loan_lend_disbursement_payment_match_ids
        elif self.payment_type == 'inbound':
            disbursement_payment_match_ids = self.loan_borrow_disbursement_payment_match_ids
        return disbursement_payment_match_ids

    def _get_disbursements(self):
        disbursement_ids = False
        disbursement_payment_match_ids = self._get_disbursement_payment_matches()
        if disbursement_payment_match_ids:
            disbursement_ids = disbursement_payment_match_ids.mapped('disbursement_id')
        return disbursement_ids

    def _get_loan_account(self):
        return self._get_disbursements()[0].account_id

    def create_account_move(self):
        if float_compare(self.amount, self.matched_amount, precision_rounding=self.currency_id.rounding) == 1:
            raise ValidationError(_("Payments that are not fully matched with disbursements may not be able to get posted."))
        disbursement_ids = self._get_disbursements()
        if not disbursement_ids:
            raise (_("No disbursement found for payment journal entry creation. Please try to match the payment with disbursement(s) first."))
        return self.env['account.move'].create(self._parepare_account_move_data())

    def match_payments(self, disbursement_ids):
        disbursement_ids.match_payments(self)

    @api.model
    def _get_not_match_err_msg(self):
        return _("Payments that are not fully matched with loan disbursement(s) may not be able to get posted into accounting system."
                 " You may need to register the payment from Disbursement menu entry...")

    def _prepare_acc_move_lines_data(self):
        data = super(LoanDisbursementPayment, self)._prepare_acc_move_lines_data()
        amount, amount_currency, diff_currency, possitive_amount = self._prepare_amounts()
        # split loan line into multiple lines corresponding to the payment matches
        ctx = dict(self._context, lang=self.partner_id.lang)
        new_lines = []
        payment_ref = []
        debit_sum = 0.0
        credit_sum = 0.0
        for payment_match in self._get_disbursement_payment_matches():
            if float_is_zero(amount, precision_rounding=self.company_id.currency_id.rounding):
                continue
            disbursement_id = payment_match.disbursement_id
            # get all refunds that still have to_pay_amount being other than zero
            refund_precision_rounding = self.currency_id.rounding if diff_currency else self.company_id.currency_id.rounding
            refund_ids = disbursement_id.refund_line_ids.filtered(lambda rl: not float_is_zero(rl.to_pay_amount, precision_rounding=refund_precision_rounding))
            # prepare matched_amt and amount currency for loan lines
            if diff_currency:
                to_pay_amount_currency = sum(refund_ids.mapped('to_pay_amount')) if possitive_amount else -1.0 * sum(refund_ids.mapped('to_pay_amount'))
                to_pay_amount = self.currency_id.with_context(ctx)._convert(to_pay_amount_currency, self.company_id.currency_id, self.company_id, self.payment_date)
                # take a part of the amount that is not greater than the to_pay_amount
                matched_amt = to_pay_amount if float_compare(abs(amount), abs(to_pay_amount), precision_rounding=self.company_id.currency_id.rounding) == 1 else amount

                matched_amt_currency = to_pay_amount_currency if float_compare(amount_currency, to_pay_amount_currency, precision_rounding=self.currency_id.rounding) == 1 else amount_currency
                amount_currency -= matched_amt_currency
            else:  # company currency
                to_pay_amount = sum(refund_ids.mapped('to_pay_amount')) if possitive_amount else -1.0 * sum(refund_ids.mapped('to_pay_amount'))
                # take a part of the amount that is not greater than the to_pay_amount
                matched_amt = to_pay_amount if float_compare(abs(amount), abs(to_pay_amount), precision_rounding=self.company_id.currency_id.rounding) == 1 else amount
                matched_amt_currency = 0.0  # force zero

            amount -= matched_amt
            refund_ids_count = len(refund_ids)
            i = 0
            for refund_id in refund_ids:
                i += 1
                if float_is_zero(matched_amt, precision_rounding=self.company_id.currency_id.rounding):
                    continue

                if diff_currency:
                    to_pay_amount = self.currency_id.with_context(ctx)._convert(refund_id.to_pay_amount, self.company_id.currency_id, self.company_id, self.payment_date)
                    to_pay_amount = to_pay_amount if possitive_amount else -1.0 * to_pay_amount
                else:
                    to_pay_amount = refund_id.to_pay_amount if possitive_amount else -1.0 * refund_id.to_pay_amount

                new_amount_currency = 0.0
                if diff_currency:
                    to_pay_amount_currency = refund_id.to_pay_amount if possitive_amount else -1.0 * refund_id.to_pay_amount
                    if float_compare(abs(matched_amt_currency), abs(to_pay_amount_currency), precision_rounding=self.currency_id.rounding):
                        new_amount_currency = to_pay_amount_currency
                    else:
                        new_amount_currency = matched_amt_currency

                if float_compare(abs(matched_amt), abs(to_pay_amount), precision_rounding=self.company_id.currency_id.rounding) == 1 and i < refund_ids_count:
                    new_amount = to_pay_amount
                else:
                    new_amount = matched_amt

                debit = -1.0 * new_amount if not possitive_amount else 0.0
                debit_sum += debit
                credit = new_amount if possitive_amount else 0.0
                credit_sum += credit

                # decrease for the next iteration
                matched_amt -= new_amount
                matched_amt_currency -= new_amount_currency

                date_maturity = refund_id.date_maturity or disbursement_id.expected_refund_date or disbursement_id.order_id.date_end
                new_line = data[0][2].copy()
                update_data = {
                    'date_maturity': date_maturity,
                    'debit': debit,
                    'credit': credit,
                    'ref': _("Disbursement Payment %s") % (disbursement_id.name,),
                    # 'loan_disbursement_id': disbursement_id.id,
                    'name': disbursement_id.name,
                    }
                if diff_currency:
                    if float_compare(credit, 0.0, precision_rounding=self.company_id.currency_id.rounding) == 1:
                        update_data['amount_currency'] = -1.0 * abs(new_amount_currency)
                    elif float_compare(debit, 0.0, precision_rounding=self.company_id.currency_id.rounding) == 1:
                        update_data['amount_currency'] = abs(new_amount_currency)

                new_line.update(update_data)
                new_lines.append((0, 0, new_line))
                payment_ref.append(disbursement_id.name)

        data[1][2]['name'] = _("Disbursement Payment")
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

    def action_post(self):
        for r in self:
            disbursement_ids = r._get_disbursements()
            if disbursement_ids:
                paid_disbursement_ids = disbursement_ids.filtered(lambda d: float_compare(d.paid_amount, d.amount, d.currency_id.rounding) == 0)
                if paid_disbursement_ids:
                    paid_disbursement_ids.with_context(full_payment_date=r.payment_date).action_paid()
        super(LoanDisbursementPayment, self).action_post()

    def action_cancel(self):
        super(LoanDisbursementPayment, self).action_cancel()
        for x in self.mapped('loan_borrow_disbursement_payment_match_ids'):
            if x.disbursement_id.to_receive_amount <= 0:
                x.disbursement_id.write({
                    'state': 'paid',
                })
            else:
                x.disbursement_id.write({
                    'state': 'confirmed',
                })

        # self.mapped('loan_lend_disbursement_payment_match_ids').unlink()
        # self.mapped('loan_borrow_disbursement_payment_match_ids').unlink()

