import ast

from odoo import models, api, fields, _
from odoo.tools import float_compare, float_is_zero, format_amount
from odoo.exceptions import UserError, ValidationError


class AbstractLoanRefund(models.AbstractModel):
    _name = 'abstract.loan.refund'
    _inherit = ['abstract.loan.line', 'mail.activity.mixin']
    _description = 'Share business logics between loan refund models'
    _order = 'date asc, id'

    state = fields.Selection(selection_add=[('cancelled', 'Cancelled')], tracking=True,
                             ondelete={'cancelled': 'cascade'},
                             help="- Draft: the principal refund is just a draft for reviews before confirmation\n"
                                  "- Confirmed: the principal refund is confirmed but no payment is made\n"
                                  "- Paid: the principal refund is paid and encoded into the accounting system with a journal entry.\n"
                                  "- Cancelled: This principal refund was cancelled.")

    paid_amount = fields.Monetary(string='Paid Amount', compute='_compute_paid_amount', store=True,
                                  help="The actual amount that have been paid for this disbursement.")

    to_pay_amount = fields.Monetary(string='To-Pay Amount', compute='_compute_to_pay_amount', store=True)

    payment_ids = fields.Many2many('loan.refund.payment', string='Payments')
    move_ids = fields.Many2many('account.move', string="Journal Entries")
    moves_count = fields.Integer(string='Journal Entries Count', compute='_compute_moves_count')

    @api.depends('payment_match_ids.payment_id')
    def _compute_payment_ids(self):
        for r in self:
            r.payment_ids = r.payment_match_ids.mapped('payment_id')

    @api.depends('payment_ids.move_id')
    def _compute_move_ids(self):
        for r in self:
            r.move_ids = r.payment_ids.mapped('move_id')

    def _compute_moves_count(self):
        for r in self:
            r.moves_count = len(r.move_ids)

    def action_view_moves(self):
        move_ids = self.mapped('move_ids')
        action = self.env.ref('account.action_move_journal_line').read()[0]
        # erase context
        action['context'] = {}
        if len(move_ids) > 1:
            action['domain'] = [('id', 'in', move_ids.ids)]
        elif len(move_ids) == 1:
            res = self.env.ref('account.view_move_form')
            action['views'] = [(res and res.id or False, 'form')]
            action['res_id'] = move_ids.ids[0]

        return action

    @api.constrains('amount', 'disbursement_id')
    def _check_amount_vs_disbursement(self):
        for r in self:
            total_refund = sum(r.disbursement_id.mapped('refund_line_ids.amount'))
            if float_compare(total_refund, r.disbursement_id.amount, precision_rounding=r.currency_id.rounding) == 1:
                raise ValidationError(
                    _("You must not have total refund amount that is greater that the associated disbursement amount (%s)."
                      " You were trying to add %s to make the total refund amount %s.")
                    % (
                        format_amount(r.env, r.disbursement_id.amount, r.currency_id),
                        format_amount(r.env, r.amount, r.currency_id),
                        format_amount(r.env, total_refund, r.currency_id)
                    )
                    )

    @api.depends('payment_match_ids.matched_amount')
    def _compute_paid_amount(self):
        for r in self:
            r.paid_amount = sum(r.payment_match_ids.mapped('matched_amount'))

    @api.depends('amount', 'paid_amount')
    def _compute_to_pay_amount(self):
        for r in self:
            r.to_pay_amount = r.amount - r.paid_amount

    def _prepare_payment_match_data(self, payment_id, matched_amount):
        data = super(AbstractLoanRefund, self)._prepare_payment_match_data(payment_id, matched_amount)
        data.update({
            'refund_id': self.id,
        })
        return data

    def action_confirm(self):
        for r in self:
            if r.order_id.state != 'confirmed':
                raise UserError(
                    _("You may not be able to confirm the refund '%s' while its contract (Ref.: %s) is not in"
                      " Confirmed state.") % (r.name, r.order_id.name))
            if r.disbursement_id.state != 'paid':
                raise UserError(
                    _("You may not be able to confirm the refund '%s' while the original disbursement (Ref.: %s) is not in"
                      " Paid state.") % (r.name, r.disbursement_id.name))
            if not r.date:
                raise UserError(_("Date is required"))
            if r.date <= r.disbursement_id.date:
                raise UserError(
                    _("You may not be able to confirm the refund %s while the date of which is earlier than its associated disbursement's date") % _(
                        r.disbursement_id.name))

        super(AbstractLoanRefund, self).action_confirm()

    def action_paid(self):
        super(AbstractLoanRefund, self).action_paid()
        disbursement_ids = self.mapped('disbursement_id')
        disbursement_ids.filtered(
            lambda d: float_is_zero(d.to_refund_amount, precision_rounding=d.currency_id.rounding)).action_refund()

    def match_payments(self, payment_ids):
        super(AbstractLoanRefund, self).match_payments(payment_ids)
        disbursement_ids = self.mapped('disbursement_id')
        disbursement_ids.with_context(regenerate=True).action_generate_interest()

    def action_cancel(self):
        for r in self:
            if any(payment.state not in ('draft', 'cancelled') for payment in r.payment_ids):
                raise UserError(
                    _("You may not be able to cancel the refund %s while its payments status is neither Draft nor Cancelled."
                      " Please cancel those payments first") % (r.name,))
            to_del_payment_ids = r.payment_ids.filtered(lambda p: p.state == 'cancelled')
            to_del_payment_ids.action_draft()
            to_del_payment_ids.unlink()
        self.write({
            'state': 'cancelled'
        })

    def _get_refund_payment_action_xml_id(self):
        raise ValidationError(
            _("The method `_get_refund_payment_action_xml_id()` has not been implemented for the model '%s' yet") % (
            self._name,))

    def action_refund_register_wizard(self):
        refund_ids = self.filtered(lambda l: l.state == 'confirmed')
        action = self.env.ref(self._get_refund_payment_action_xml_id()).read()[0]
        ctx = ast.literal_eval(action['context'])
        ctx.update({'default_refund_ids': refund_ids.ids})
        action['context'] = ctx
        return action
