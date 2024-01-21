from odoo import models, fields, api, _
from odoo.tools import float_is_zero, float_compare
from odoo.exceptions import UserError, ValidationError, _logger


class LoanMixin(models.AbstractModel):
    _name = 'loan.mixin'
    _description = 'Loan Mixin'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid')], default='draft', string='Status', tracking=True, required=True, copy=False, index=True)
    name = fields.Char(string='Ref.', required=True, default='/',copy=False, readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, states={'draft': [('readonly', False)]})
    date_maturity = fields.Date(string='Due Date', readonly=True, states={'draft': [('readonly', False)]})
    date_confirmed = fields.Date(string='Date Confirmed', tracking=True, readonly=True, states={'draft': [('readonly', False)]})

    def _prepare_payment_match_data(self, payment_id, matched_amount):
        return {
            'payment_id': payment_id.id,
            'matched_amount': matched_amount,
            }

    def _get_payment_match_model(self):
        raise ValidationError(_("The method `_get_payment_match_model()` has not been implemented for the model '%s' yet") % (self._name,))

    def match_payments(self, payment_ids):
        PaymentMatch = self.env[self._get_payment_match_model()]
        for r in self:
            for payment_id in payment_ids:
                unmatched_amt = r.amount - r.paid_amount
                payment_unmatched_amt = payment_id.amount - payment_id.matched_amount
                if float_is_zero(unmatched_amt, precision_rounding=r.currency_id.rounding):
                    continue
                if  float_is_zero(payment_unmatched_amt, precision_rounding=r.currency_id.rounding):
                    payment_ids -= payment_id
                    continue

                amount_compare = float_compare(unmatched_amt, payment_unmatched_amt, precision_rounding=r.currency_id.rounding)

                # unmatched_amt >= payment_unmatched_amt
                if amount_compare >= 0:
                    PaymentMatch.create(r._prepare_payment_match_data(payment_id, payment_unmatched_amt))
                    payment_ids -= payment_id
                    if amount_compare == 0:
                        break
                # unmatched_amt < payment_unmatched_amt
                else:
                    PaymentMatch.create(r._prepare_payment_match_data(payment_id, unmatched_amt))
                    break

    def action_confirm(self):
        for r in self:
            if r.state != 'draft':
                raise UserError(_("You may not be able to confirm the document '%s' which is not in Draft state!") % (r.name,))
        date_confirmed = self.env.context.get('date_confirmed', False) or fields.Date.today()
        self.write({
            'state': 'confirmed',
            'date_confirmed': date_confirmed
            })

    def action_paid(self):
        for r in self:
            if r.state != 'confirmed':
                raise UserError(_("You may not be able to confirm the document '%s' which is not in Confirmed state!") % (r.name,))

        self.write({
            'state':'paid',
        })

    def action_re_confirm(self):
        for r in self:
            if r.state != 'paid':
                raise UserError(_("You may not be able to re-confirm the document '%s' which is not in Paid state!") % (r.name,))
        self.write({
            'state':'confirmed',
        })

    def action_draft(self):
        for r in self:
            if r.state != 'cancelled':
                raise UserError(_("You may not  be able to set to draft the document '%s' which is not in cancelled state. Please cancel it first."))
        self.write({
            'state':'draft',
            'date_confirmed': False,
            })

    def unlink(self):
        for r in self:
            if r.state != 'draft':
                raise UserError(_("The document '%s' must be in Draft state to get deleted. Please set it to Draft first!")
                                % (r.name,))
        return super(LoanMixin, self).unlink()

    def _get_sequence(self):
        raise ValidationError(_("The method `_get_sequence()` has not been implemented for the model '%s' yet!") % (self._name,))

    @api.model_create_multi
    def create(self, vals_list):
        if self._name != 'loan.borrow.disbursement':
            for vals in vals_list:
                if vals.get('name', '/') == '/':
                    vals['name'] = self._get_sequence() or '/'
        return super(LoanMixin, self).create(vals_list)
