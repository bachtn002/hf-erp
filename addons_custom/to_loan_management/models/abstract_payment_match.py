from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class AbstractPaymentMatch(models.AbstractModel):
    _name = 'abstract.payment.match'
    _description = "Share business logics between payment match models"

    matched_amount = fields.Monetary(string='Matched Amount', required=True, help="The matching amount between loan payment"
                                  " and a loan disbursement")
    currency_id = fields.Many2one('res.currency', string='Currency')

    def get_payment_matches_field(self):
        raise ValidationError(_("The method `get_payment_matches_field()` has not been implemented for the model '%s' yet") % (self._name,))

    @api.constrains('payment_id', 'matched_amount')
    def _check_matched_amount_vs_payment_amount(self):
        for r in self:
            if float_compare(r.matched_amount, r.payment_id.amount, precision_rounding=r.currency_id.rounding) == 1:
                raise ValidationError(_("Matched Amount must not be greater than the payment amount."))

    @api.model_create_multi
    def create(self, vals_list):
        matches = super(AbstractPaymentMatch, self).create(vals_list)
        for match in matches:
            LoanPayment = match.payment_id
            payments = LoanPayment.search([(self.get_payment_matches_field(), 'in', [match.id])])
            for payment in payments:
                if float_compare(payment.matched_amount, payment.amount, precision_rounding=payment.currency_id.rounding) == 0:
                    payment.action_set_matched()
        return matches
