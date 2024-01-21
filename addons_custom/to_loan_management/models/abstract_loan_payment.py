from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class AbstractLoanPayment(models.AbstractModel):
    _name = 'abstract.loan.payment'
    _inherit = 'mail.thread'
    _description = 'Loan Payment Abstract'
    _order = 'payment_date asc, id'
#     _inherit = 'account.abstract.payment'

    name = fields.Char(string='Ref.', readonly=True, copy=False, default="Draft Payment")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('matched', 'Matched'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status", tracking=True)
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], string='Payment Type', required=True)
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method Type', required=True)
    payment_method_code = fields.Char(related='payment_method_id.code',
        help="Technical field used to adapt the interface to the payment type selected.", readonly=True)

    partner_type = fields.Selection([('lender', 'Lender'), ('borrower', 'Borrower')], string='Partner Type', required=True,
                                    help="The type of the loan partner:\n"
                                    "- Lender: The one who lend you. Also known as financing vendor"
                                    "- Borrower: The one who borrow you. Also known as financing customer")
    partner_id = fields.Many2one('res.partner', string='Partner')

    amount = fields.Monetary(string='Payment Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id)
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True, copy=False)
    communication = fields.Char(string='Memo')
    journal_id = fields.Many2one('account.journal', string='Payment Journal', required=True, domain=[('type', 'in', ('bank', 'cash'))])
    company_id = fields.Many2one('res.company', string='Company')

    hide_payment_method = fields.Boolean(compute='_compute_hide_payment_method',
        help="Technical field used to hide the payment method if the selected journal has only one available which is 'manual'")
    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True)
    description = fields.Char(string='Description', size=500)
    beneficiary_bank_id = fields.Many2one('res.partner.bank', string='beneficiary bank')

    @api.constrains('amount')
    def _check_amount(self):
        for r in self:
            if not float_compare(r.amount, 0.0, precision_rounding=r.currency_id.rounding) == 1:
                raise ValidationError(_('The payment amount must be strictly positive.'))

    @api.depends('payment_type', 'journal_id')
    def _compute_hide_payment_method(self):
        for r in self:
            if not r.journal_id:
                r.hide_payment_method = True
                return
            journal_payment_methods = r.payment_type == 'inbound' and r.journal_id.inbound_payment_method_ids or r.journal_id.outbound_payment_method_ids
            r.hide_payment_method = len(journal_payment_methods) == 1 and journal_payment_methods[0].code == 'manual'

    @api.onchange('journal_id')
    def _onchange_journal(self):
        if self.journal_id:
            self.currency_id = self.journal_id.currency_id or self.company_id.currency_id
            # Set default payment method (we consider the first to be the default one)
            payment_methods = self.payment_type == 'inbound' and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
            self.payment_method_id = payment_methods and payment_methods[0] or False
            # Set payment method domain (restrict to methods enabled for the journal and to selected payment type)
            payment_type = self.payment_type in ('outbound', 'transfer') and 'outbound' or 'inbound'
            return {'domain': {'payment_method_id': [('payment_type', '=', payment_type), ('id', 'in', payment_methods.ids)]}}
        return {}

    def _parepare_account_move_data(self):
        lines_data = self._prepare_acc_move_lines_data()
        return {
            'ref': self.communication,
            'line_ids': lines_data,
            'journal_id': self.journal_id.id,
            'date': self.payment_date,
            }

    def _prepare_payment_data(self):
        return {
            'partner_type': self.partner_type,
            'partner_id': self.partner_id.id,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'payment_method_id': self.payment_method_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,
            }


    def _prepare_payment_by_amount_data(self,amount):
        return {
            'partner_type': self.partner_type,
            'partner_id': self.partner_id.id,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'payment_method_id': self.payment_method_id.id,
            'amount': amount,
            'currency_id': self.currency_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,
            }

    def _prepare_amounts(self):
        ctx = dict(self._context, lang=self.partner_id.lang)
        company_currency = self.company_id.currency_id
        diff_currency = self.currency_id != company_currency
        if diff_currency:
            amount_currency = self.amount
            amount = self.currency_id.with_context(ctx)._convert(self.amount, company_currency, self.company_id, self.payment_date)
        else:
            amount_currency = False
            amount = self.amount

        if self.payment_type == 'outbound':
            amount = -1 * amount
            amount_currency = -1 * amount_currency

        possitive_amount = float_compare(amount, 0.0, precision_rounding=self.currency_id.rounding) == 1
        return amount, amount_currency, diff_currency, possitive_amount

    def _get_loan_account(self):
        raise ValidationError(_("The method `_get_loan_account()` has not been implemented for the model '%'") * (self._name,))

    def _prepare_acc_move_lines_data(self):
        amount, amount_currency, diff_currency, possitive_amount = self._prepare_amounts()
        loan_account_id = self._get_loan_account()
        object_cost_id = False
        part_id = False
        analytic_account_id = False
        if 'loan_borrow_disbursement_payment_match_ids' in self and len(self.loan_borrow_disbursement_payment_match_ids) > 0:
            object_cost_id = self.loan_borrow_disbursement_payment_match_ids[0].order_id.object_cost_id.id
            part_id = self.loan_borrow_disbursement_payment_match_ids[0].order_id.part_id.id
            analytic_account_id = self.loan_borrow_disbursement_payment_match_ids[0].order_id.analytic_account_id.id
        # loan line
        line1 = {
            'date_maturity': self.payment_date,
            'partner_id': self.partner_id.commercial_partner_id.id,
            'name': self.name,
            'date': self.payment_date,
            'debit':-1.0 * amount if not possitive_amount else 0.0,
            'credit': amount if possitive_amount else 0.0,
            'account_id': loan_account_id.id,
            'currency_id': diff_currency and self.currency_id.id,
            'ref': self.communication,
            # 'object_cost_id': object_cost_id,
            'analytic_account_id': analytic_account_id,
        }
        if diff_currency:
            if float_compare(line1['credit'], 0.0, precision_rounding=self.company_id.currency_id.rounding) == 1:
                line1['amount_currency'] = -1.0 * abs(amount_currency)
            elif float_compare(line1['debit'], 0.0, precision_rounding=self.company_id.currency_id.rounding) == 1:
                line1['amount_currency'] = abs(amount_currency)

        # loan payment line
        line2 = {
            'date_maturity': self.payment_date,
            'partner_id': self.partner_id.commercial_partner_id.id,
            'name': self.name,
            'date': self.payment_date,
            'debit': amount if possitive_amount else 0.0,
            'credit':-1.0 * amount if not possitive_amount else 0.0,
            'account_id': self.journal_id.payment_credit_account_id.id if possitive_amount else self.journal_id.payment_debit_account_id.id,
            'currency_id': diff_currency and self.currency_id.id,
            'ref': self.communication,
            # 'object_cost_id': object_cost_id,
            'analytic_account_id': analytic_account_id,
        }
        if diff_currency:
            if float_compare(line2['credit'], 0.0, precision_rounding=self.company_id.currency_id.rounding) == 1:
                line2['amount_currency'] = -1.0 * abs(amount_currency)
            elif float_compare(line2['debit'], 0.0, precision_rounding=self.company_id.currency_id.rounding) == 1:
                line2['amount_currency'] = abs(amount_currency)

        return [(0, 0, line1), (0, 0, line2)]

    def action_set_matched(self):
        # for r in self:
        #     if r.state != 'draft':
        #         raise ValidationError(_("You can not set payment as matched while its state is not Draft"))
        self.write({'state':'matched'})

    def unlink(self):
        for r in self:
            if r.state != 'draft':
                raise ValidationError(_("You may not be able to delete the payment '%s' while its state is not Draft") % (r.name,))
        return super(AbstractLoanPayment, self).unlink()

    def action_cancel(self):
        for r in self:
            if r.state not in ('matched', 'posted'):
                raise ValidationError(_("You may not be able to cancel the payment '%s' while its state is neither Matched nor Posted.") % (r.name,))
        move_ids = self.mapped('move_id')
        move_ids.button_draft()
        move_ids.button_cancel()
        move_ids.with_context(force_delete=True).unlink()
        self.write({'state':'cancelled'})

    def action_draft(self):
        for r in self:
            if r.state != 'cancelled':
                raise ValidationError(_("You can not set payment as Draft while its state is not Cancelled"))
        self.write({'state':'draft'})

    def _get_not_match_err_msg(self):
        return _("Payments that are not fully matched may not be able to get posted.")

    def action_post(self):
        for r in self:
            if float_compare(r.amount, r.matched_amount, precision_rounding=r.currency_id.rounding) == 1:
                raise ValidationError(self._get_not_match_err_msg())
            move_id = r.create_account_move()
            move_id.post()
            r.write({
                'move_id': move_id.id,
                'name': move_id.name
                })
        self.write({'state':'posted'})
