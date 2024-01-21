import ast

from dateutil.relativedelta import relativedelta
from dateutil import rrule

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_round, float_is_zero, format_amount


class AbstractLoanDisbursement(models.AbstractModel):
    _name = 'abstract.loan.disbursement'
    _description = 'Disbursement Plan Line'
    _inherit = ['abstract.loan.line', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    state = fields.Selection(selection_add=[('refunded', 'Refunded'), ('cancelled', 'Cancelled')], tracking=True,
                             ondelete={'refunded': 'cascade', 'cancelled': 'cascade'},
                             help="- Draft: the disbursement is just a draft for reviews before confirmation\n"
                                  "- Confirmed: the disbursement is confirmed but no payment is made\n"
                                  "- Paid: the disbursement is paid and encoded into the accounting system with a journal entry.\n"
                                  "- Cancelled: This disbursement was cancelled.")

    account_id = fields.Many2one('account.account', string='Loan Account', readonly=True)

    expected_refund_date = fields.Date(string='Refund Date', tracking=True,
                                       help="The date on which this loan amount is expected to be refunded. If not specified, the contract end date will be proposed.")
    full_refunded_date = fields.Date(string='Fully Refunded Date', compute='_compute_fully_refunded_date')
    journal_id = fields.Many2one('account.journal', string='Journal', readonly=True,
                                 states={'draft': [('readonly', False)]})

    paid_amount = fields.Monetary(string='Received Amount', compute='_compute_paid_amount', store=True,
                                  help="The actual amount that have been paid for this disbursement.")

    to_receive_amount = fields.Monetary(string='To-Receive Amount', compute='_compute_to_receive_amount', store=True)
    to_refund_amount = fields.Monetary(string='To-Refund Amount', compute='_compute_to_refund_amount', store=True)

    payment_ids = fields.Many2many('loan.disbursement.payment', string='Payments')
    move_ids = fields.Many2many('account.move', string="Journal Entries")
    moves_count = fields.Integer(string='Journal Entries Count', compute='_compute_moves_count')
    last_interest_date_to = fields.Date(string="Last Interest Date", compute='_compute_last_interest_date_to',
                                        store=True,
                                        help="The technical field to store Date To value of the last Loan Interest line of this disbursement")

    loan_duration = fields.Integer(string='Loan Duration', default=12,
                                   readonly=True, states={'draft': [('readonly', False)]},
                                   help="The duration (in months) of the loan contract.")
    date_end = fields.Date(string='Contract End', tracking=True, compute='_compute_date_end', store=True, readonly=True,
                           help="The date on which this contract will become expired")
    date_start = fields.Date(string='Start Date',
                             states={'confirmed': [('readonly', True)], 'done': [('readonly', True)],
                                     'cancelled': [('readonly', True)]},
                             help="The date on which the first of the loan is expected to be released")

    @api.depends('date_start', 'loan_duration')
    def _compute_date_end(self):
        for r in self:
            if r.date_start and r.loan_duration:
                r.date_end = r.date_start + relativedelta(months=+r.loan_duration)

    def _compute_fully_refunded_date(self):
        for r in self:
            if r.state == 'refunded':
                r.full_refunded_date = r.refund_line_ids.get_payment_dates()[-1]
            else:
                r.full_refunded_date = False

    def get_refund_dates(self):
        """
        @requires: [datetime.date] list of date objects
        """
        dates = []
        for r in self:
            dates += r.refund_line_ids.get_payment_dates()
            if r.state != 'refunded':
                dates.append(r.get_refund_expected_start_date())
        dates = list(set(dates))
        dates.sort()
        return dates

    def get_refund_expected_start_date(self):
        """
        @return: datetime.date
        """
        if self.expected_refund_date:
            return self.expected_refund_date
        if self.date_end:
            order_refund_start = self.date_end
        elif self.order_id.principal_refund_method == 'end_contract':
            order_refund_start = self.order_id.date_end
        else:
            order_refund_start = self.order_id.principal_refund_start_date
        disbursment_date = self.get_disbursement_date()
        refund_start_date = disbursment_date if disbursment_date > order_refund_start else order_refund_start
        return refund_start_date

    def get_last_interest(self):
        """
        Return the last interest of the disbursement
        """
        if self.interest_line_ids:
            return self.interest_line_ids[-1]
        else:
            return self.interest_line_ids

    @api.depends('interest_line_ids.date_to')
    def _compute_last_interest_date_to(self):
        for r in self:
            last_interest_id = r.get_last_interest()
            if last_interest_id:
                r.last_interest_date_to = last_interest_id.date_to
            else:
                r.last_interest_date_to = False

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

    @api.depends('payment_match_ids.payment_id')
    def _compute_payment_ids(self):
        for r in self:
            r.payment_ids = r.payment_match_ids.mapped('payment_id')

    @api.depends('payment_ids.move_id')
    def _compute_move_ids(self):
        for r in self:
            r.move_ids = r.payment_ids.mapped('move_id')

    @api.depends('refund_line_ids.to_pay_amount', 'amount')
    def _compute_to_refund_amount(self):
        for r in self:
            if r.refund_line_ids and r.state != 'draft':
                r.to_refund_amount = sum(r.refund_line_ids.mapped('to_pay_amount'))
            else:
                r.to_refund_amount = r.amount

    @api.depends('amount', 'paid_amount')
    def _compute_to_receive_amount(self):
        for r in self:
            r.to_receive_amount = r.amount - r.paid_amount

    @api.depends('payment_match_ids.matched_amount', 'payment_match_ids.payment_state')
    def _compute_paid_amount(self):
        for r in self:
            paid_amount = 0.0
            for line in r.payment_match_ids:
                if line.payment_state not in ('draft', 'cancelled'):
                    paid_amount += line.matched_amount
            r.paid_amount = paid_amount

    @api.constrains('amount', 'order_id', 'state')
    def _check_total_disbursement(self):
        for r in self:
            disbursement_line_ids = r.order_id.disbursement_line_ids.filtered(
                lambda l: l.state in ('draft', 'cancelled'))
            total_disbursement = sum(disbursement_line_ids.mapped('amount'))
            if float_compare(total_disbursement, r.order_id.loan_amount,
                             precision_rounding=r.currency_id.rounding) == 1:
                raise ValidationError(
                    _("You must not have total disbursement amount that is greater that the contract's loan amount (%s)."
                      " You were trying to add %s to make the total disbursement amount %s.")
                    % (
                        format_amount(r.env, r.order_id.loan_amount, r.order_id.currency_id),
                        format_amount(r.env, r.amount, r.order_id.currency_id),
                        format_amount(r.env, total_disbursement, r.order_id.currency_id)
                    )
                )

    def get_disbursement_date(self):
        return self.full_payment_date or self.order_id.get_first_disbursement_date() or self.date_maturity

    def _prepare_payment_match_data(self, payment_id, matched_amount):
        data = super(AbstractLoanDisbursement, self)._prepare_payment_match_data(payment_id, matched_amount)
        data.update({
            'disbursement_id': self.id,
        })
        return data

    def get_number_of_refunds(self):
        number = 0
        if self.order_id.principal_refund_method == 'end_contract':
            number = 1
        elif self.order_id.principal_refund_method == 'number':
            number = self.order_id.principal_refund_method_number
        return number

    def _prepare_refund_line_data(self, amount, date, date_maturity, refund_id=None):
        data = {
            'disbursement_id': self.id,
            'amount': amount,
            'date': date,
            'date_maturity': date_maturity
        }
        if refund_id:
            data['refund_id'] = refund_id
        return data

    def _get_refund_line_model(self):
        raise ValidationError(
            _("The method `_get_refund_line_model()` has not been implemented for the model '%s' yet") % (self._name,))

    def _get_loan_interest_line_model(self):
        raise ValidationError(
            _("The method `_get_loan_interest_line_model()` has not been implemented for the model '%s' yet") % (
                self._name,))

    def get_loan_at_date(self, date):
        if not self.refund_line_ids:
            return self.amount
        else:
            amount = self.amount
            for refund_line_id in self.refund_line_ids:
                if refund_line_id.payment_match_ids:
                    for payment_match in self.mapped('refund_line_ids.payment_match_ids').filtered(
                            lambda pm: pm.payment_id.payment_date <= date):
                        amount -= payment_match.matched_amount
                else:
                    if refund_line_id.date <= date:
                        amount -= refund_line_id.amount

            #             refunded_line_ids = self.refund_line_ids.filtered(lambda l: l.date <= date)
            #             if refunded_line_ids:
            #                 refunded_amount = sum(refunded_line_ids.mapped('amount'))
            #                 amount -= refunded_amount
            return amount

    def match_payments(self, payment_ids):
        super(AbstractLoanDisbursement, self).match_payments(payment_ids)
        self.with_context(regenerate=True).action_generate_refund_lines()

    def action_generate_refund_lines(self):
        regenerate = self.env.context.get('regenerate', False)
        self = self.with_context(regenerate=regenerate)
        self._generate_refund_lines()
        self.action_generate_interest()

    def _generate_refund_lines(self):
        refund_line_ids = self.env[self._get_refund_line_model()]
        if self.env.context.get('regenerate', False):
            self.mapped('refund_line_ids').filtered(lambda l: l.state == 'draft').unlink()
        for r in self.filtered(
                lambda l: not float_is_zero(l.to_refund_amount, precision_rounding=l.currency_id.rounding)):
            #             ignored_dates = r.mapped('refund_line_ids.date') # we don't want to create refunds that overlap the ex
            order_id = r.order_id
            nbr_refunds = r.get_number_of_refunds()
            if order_id.principal_refund_method == 'number':
                to_refund_amount = r.to_refund_amount
                amount = float_round(r.to_refund_amount / nbr_refunds, precision_rounding=r.currency_id.rounding)
                if self.date_start:
                    date_start = self.date_start
                else:
                    date_start = r.get_refund_dates()[0]

                for i in range(nbr_refunds):
                    # last refund line
                    if i == nbr_refunds - 1:
                        amount = to_refund_amount - (nbr_refunds - 1) * amount
                    #                     if date_start in ignored_dates:
                    #                         continue
                    refund_line_ids.create(r._prepare_refund_line_data(amount, date_start, date_start))
                    date_start = date_start + relativedelta(months=order_id.principal_refund_method_period)

            elif order_id.principal_refund_method == 'end_contract':
                refund_line_ids.create(r._prepare_refund_line_data(r.amount, order_id.date_end, order_id.date_end))

    def _get_dates_for_interests(self):
        """
        This method return dates to prepare interest data
        """

        # Initiate with refund payment dates
        dates = self.get_refund_dates()
        if not self.order_id.interest_incl_refund_date:
            # refund dates should be excluded, hence, we minus one day
            # for example, we refund on July 20, the interest should be counted to and included July 19 only.
            dates = [date - relativedelta(days=1) for date in dates]

        payment_dates = self.get_payment_dates()
        if not self.order_id.interest_incl_disburment_date:
            # disbursment dates should be excluded, hence, we plus one day
            # for example, we receive disbursment on July 20, the interest should be counted from and included July 21 only.
            payment_dates = [date + relativedelta(days=1) for date in payment_dates]

        dates += payment_dates
        dates.sort()
        first_date = dates[0]
        last_date = dates[-1]
        dates = set(dates)

        # find last date of floating rate lines
        if self.order_id.interest_rate_type_id.type == 'floating':
            rate_line_ids = self.env['loan.floating.rate'].search([
                ('interest_date_type_id', '=', self.order_id.interest_rate_type_id.id),
                ('date_from', '<=', last_date),
                '|', ('date_to', '=', False), ('date_to', '>', first_date)], order='date_from desc')
            for line in rate_line_ids:
                date_from = line.date_from
                one_day_ago = date_from - relativedelta(days=1)
                if one_day_ago >= first_date and one_day_ago <= last_date:
                    dates.add(one_day_ago)

        # iterate for dates for interest periods
        ToBase = self.env['to.base']
        dtstart = first_date
        until = last_date
        interest_period_start_day = self.order_id.interest_period_start_day

        if interest_period_start_day == 1:
            for dt in rrule.rrule(rrule.DAILY, dtstart=dtstart, until=until):
                last_date_of_period = self.order_id.find_last_date_of_period(dt)
                if not last_date_of_period in dates and last_date_of_period <= last_date:
                    dates.add(last_date_of_period)
        else:
            start_day_offset = interest_period_start_day - 1
            period_iter = ToBase.period_iter(self.order_id.interest_cycle, dtstart, until, start_day_offset)

            for dt_end in period_iter:
                if dt_end <= until:
                    dates.add(dt_end)

        dates = list(dates)
        dates.sort()
        return dates

    def _prepare_interest_data(self, date_from, date_to):

        if date_to <= self.order_id.date_end:
            interest_rate_type_id = self.order_id.interest_rate_type_id
        else:
            interest_rate_type_id = self.order_id.expiry_interest_rate_type_id

        data = {
            'rate_type_id': interest_rate_type_id.id,
            'date_from': fields.Date.to_date(date_from),
            'date_to': fields.Date.to_string(date_to),
            'date_maturity': fields.Date.to_string(date_to + relativedelta(days=self.order_id.due_day or 0)),
            'disbursement_id': self.id,
            'loan_amount': self.get_loan_at_date(date_to - relativedelta(days=1)),
        }
        if interest_rate_type_id.type == 'floating':
            rate_line_id = interest_rate_type_id.get_floating_rate_line(date_to)
            if rate_line_id:
                data['rate_line_id'] = rate_line_id.id
        return data

    def action_generate_interest(self):
        """
        Known Issue: If the first period has only one day, it will be merged into the next period
        """

        def date_in_timeframe(ignored_datetime_frame, dt):
            """
            Test if a given date is within a given timeframe
            @param ignored_datetime_frame: a list of tuple of two datetime object. E.g. [(dt1, dt2),....,(dtn,dtm)]
            @param datetime: a given datetime object to test 
            @rtype: Boolean
            """
            for line in ignored_datetime_frame:
                if dt >= line[0] and dt <= line[1]:
                    return True
            return False

        if self.env.context.get('regenerate', False):
            self.mapped('interest_line_ids').filtered(lambda l: l.state == 'draft').unlink()
        InterestLine = self.env[self._get_loan_interest_line_model()]
        for r in self:
            ignored_time_frame = r.interest_line_ids.filtered(
                lambda l: l.state in ('confirmed', 'paid')).generate_timeframe()
            date_from = False
            for date in r._get_dates_for_interests():
                date_obj = date
                if date_in_timeframe(ignored_time_frame, date):
                    date_from = date_obj + relativedelta(days=1)
                    continue
                if not date_from:
                    date_from = date
                    # If the first period has only one day which is the last day of the period
                    # we still need to create interest. Otherwise, it will be merge into the next interest period
                    if date_from == fields.Date.to_string(r.order_id.find_last_date_of_period(date_from)):
                        InterestLine.create(r._prepare_interest_data(date_from, date))
                        date_from = date_obj + relativedelta(days=1)
                    continue
                InterestLine.create(r._prepare_interest_data(date_from, date))
                date_from = date_obj + relativedelta(days=1)

    def action_confirm(self):
        for r in self:
            if r.order_id.state != 'confirmed':
                raise UserError(
                    _("You may not be able to confirm the disbursement '%s' while its contract (Ref.: %s) is not in"
                      " Confirmed state.") % (r.name, r.order_id.name))

        super(AbstractLoanDisbursement, self).action_confirm()
        self.with_context(regenerate=True).action_generate_refund_lines()

    def action_paid(self):
        for r in self:
            if not float_compare(r.paid_amount, r.amount, r.currency_id.rounding) == 0:
                raise UserError(
                    _("You may not mark a disbursement as Paid while its paid amount is not equal to its loan amount!"))
            if r.order_id.state != 'confirmed':
                raise UserError(
                    _("You may not be able to set the disbursement '%s' Paid while its contract (Ref.: %s) is not in"
                      " Confirmed state.") % (r.name, r.order_id.name))
        super(AbstractLoanDisbursement, self).action_paid()
        self = self.with_context(regenerate=True)
        self.action_generate_refund_lines()
        self.mapped('refund_line_ids').action_confirm()

    #         self.action_generate_interest()

    def action_refund(self):
        for r in self:
            if not float_compare(r.paid_amount, 0.0, r.currency_id.rounding) == 1:
                raise UserError(_("You may not be able to refund a disbursement that you have not been received yet!"))

        self.write({
            'state': 'refunded',
        })

    def action_cancel(self):
        for r in self:
            if r.state == 'paid':
                raise UserError(_("You have to unreconcile all the payments related to the disbursement %s"
                                  " before cancellation") % (r.name,))
            if r.state == 'refunded':
                raise UserError(_("You may not be able to cancel the disbursement %s while it has been refunded"
                                  " already.") % (r.name,))

            if any(payment.state not in ('draft', 'cancelled') for payment in r.payment_ids):
                raise UserError(
                    _("You may not be able to cancel the disbursement %s while its payments status is neither Draft nor Cancelled."
                      " Please cancel those payments first") % (r.name,))
            to_del_payment_ids = r.payment_ids.filtered(lambda p: p.state == 'cancelled')
            to_del_payment_ids.action_draft()
            to_del_payment_ids.unlink()

        self.write({
            'state': 'cancelled',
            'date_confirmed': False,
        })

    def _get_disbursement_payment_action_xml_id(self):
        raise ValidationError(
            _("The method `_get_disbursement_payment_action_xml_id()` has not been implemented for the model '%s' yet") % (
                self._name,))

    def action_disbursement_register_wizard(self):
        disbursement_ids = self.filtered(lambda l: l.state == 'confirmed')
        action = self.env.ref(self._get_disbursement_payment_action_xml_id()).read()[0]
        ctx = ast.literal_eval(action['context'])
        ctx.update({'default_disbursement_ids': disbursement_ids.ids, 'default_order_id': self.order_id.id})
        action['context'] = ctx
        return action

    def unlink(self):
        self.mapped('refund_line_ids').unlink()
        self.mapped('interest_line_ids').unlink()
        return super(AbstractLoanDisbursement, self).unlink()
