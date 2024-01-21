from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class AbstractRefundPaymentMatch(models.AbstractModel):
    _name = 'abstract.refund.payment.match'
    _inherit = 'abstract.payment.match'
    _description = 'Refund Payment Match Abstract'

    payment_id = fields.Many2one('loan.refund.payment', string='Payment', ondelete='cascade', required=True)
    name = fields.Char(related='payment_id.name', readonly=True)
    payment_date = fields.Date(related='payment_id.payment_date', readonly=True)
    currency_id = fields.Many2one(related='payment_id.currency_id', readonly=True, help="The matching amount between loan payment"
                                  " and a loan refund")

    @api.constrains('refund_id', 'matched_amount')
    def _check_matched_amount_vs_refund_amount(self):
        for r in self:
            if float_compare(r.matched_amount, r.refund_id.amount, precision_rounding=r.currency_id.rounding) == 1:
                raise ValidationError(_("Matched Amount must not be greater than the refund amount."))

    @api.constrains('refund_id', 'currency_id')
    def _check_currency_id_vs_refund(self):
        for r in self:
            if r.refund_id.currency_id.id != r.currency_id.id:
                raise ValidationError(_("Currency discrepancy between Refund and Payment."))

    def unlink(self):
        self.mapped('refund_id').filtered(lambda d: d.state == 'paid').action_re_confirm()
        return super(AbstractRefundPaymentMatch, self).unlink()

