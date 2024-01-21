from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class AbstractDisbursementPaymentMatch(models.AbstractModel):
    _name = 'abstract.disbursement.payment.match'
    _inherit = 'abstract.payment.match'
    _description = "Disbursment Payment Match Abstract"

    payment_id = fields.Many2one('loan.disbursement.payment', string='Payment', ondelete='cascade', required=True)
    name = fields.Char(related='payment_id.name', readonly=True)
    payment_date = fields.Date(related='payment_id.payment_date', readonly=True)
    currency_id = fields.Many2one(related='payment_id.currency_id', readonly=True)
    payment_state = fields.Selection(related='payment_id.state', readonly=True)
    description = fields.Char(related='payment_id.description', string='Description')
    beneficiary_bank_id = fields.Many2one('res.partner.bank',related='payment_id.beneficiary_bank_id', string='beneficiary bank')

    @api.constrains('disbursement_id', 'matched_amount')
    def _check_matched_amount_vs_disbursment_amount(self):
        for r in self:
            if float_compare(r.matched_amount, r.disbursement_id.amount, precision_rounding=r.currency_id.rounding) == 1:
                raise ValidationError(_("Matched Amount must not be greater than the disbursement amount."))

    @api.constrains('disbursement_id', 'payment_id')
    def _check_currency_id_vs_disbursment(self):
        for r in self:
            if r.disbursement_id.currency_id.id != r.currency_id.id:
                raise ValidationError(_("Currency discrepancy between Disbursement and Payment."))

    def unlink(self):
        self.mapped('disbursement_id').filtered(lambda d: d.state == 'paid').action_re_confirm()
        return super(AbstractDisbursementPaymentMatch, self).unlink()
