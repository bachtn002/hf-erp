from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_is_zero, format_date


class AbstractLoanInterest(models.AbstractModel):
    _name = 'abstract.loan.interest'
    _inherit = 'loan.mixin'
    _description = "Loan Interest Abstract"
    _order = 'date_to asc, id'

    state = fields.Selection(selection_add=[('cancelled', 'Canceled')], ondelete={'cancelled': 'cascade'})
    rate_type_id = fields.Many2one('loan.interest.rate.type', string='Interest Rate Type', required=True,
                                   compute='_get_rate_type', inverse='_set_rate_type', store=True)
    internal_type = fields.Selection(related='rate_type_id.type', string='Internal Type', help="The internal type of the interest,"
                                     " which is related to the type of the corresponding Interest Rate Type.")
    loan_amount = fields.Monetary(string='Loan Amount')
    date_from = fields.Date(string='Date From', required=True, index=True)
    date_to = fields.Date(string='Date To', required=True, index=True)
    nbr_of_days = fields.Integer(string='Duration (days)', compute='_compute_nbr_of_days', store=True,
                                 help="Number of days for interest computation.\n"
                                 "If the rate type is set with a fixed days of month, the Duration will not"
                                 " be greater than that fixed days of month.\n"
                                 "If the rate type is set with a fixed days of year, the Duration will not"
                                 " be greater than that fixed days of year.\n")
    daily_rate = fields.Float(string='Daily Rate(%)', digits=(26, 20), default=0.0, compute='_compute_daily_rate', store=True)
    rate_line_id = fields.Many2one('loan.floating.rate', string='Floating Rate Line',
                                   compute='_get_rate_line_id', inverse='_set_rate_line_id', store=True)

    amount = fields.Monetary(compute='_compute_amount', store=True, help="The interest amount which is automatically computed based on"
                             " the corresponding loan amount and daily rate and number of day in the duration.")

    invoiced_amount = fields.Monetary(string='Invoiced Amount')
    to_invoice_amount = fields.Monetary(string='To Invoice Amount', compute='_compute_to_invoice_amount', store=True)
    fully_invoiced = fields.Boolean(string='Fully Invoiced', compute='_compute_fully_invoiced', store=True)
    invoice_ids = fields.Many2many('account.move', string='Invoices')
    invoices_count = fields.Integer(string='Invoices Count', compute='_compute_invoices_count')
    partner_id = fields.Many2one('res.partner', string='Partner')

    _sql_constraints = [
        ('date_from_vs_date_to_check',
         'CHECK(date_from <= date_to)',
         "Date From must not be later than Date To!"),
        ]

    @api.constrains('date_from', 'date_to', 'disbursement_id')
    def _check_overlap(self):
        for r in self:
            overlap = self.search([
                ('id', '!=', r.id),
                ('date_from', '<=', r.date_to),
                ('date_to', '>=', r.date_from),
                ('disbursement_id', '=', r.disbursement_id.id),
                ], limit=1)
            if overlap:
                raise ValidationError(_("You may not be able to create a Loan Interest for the period from %s to %s that overlaps the existing"
                                        " interest %s (Date From: %s; Date To: %s). Please review the values for Date From and Date To")
                                      % (
                                          format_date(r.env, r.date_from),
                                          format_date(r.date_from),
                                          overlap.name,
                                          format_date(r.env, overlap.date_from),
                                          format_date(r.env, overlap.date_to)
                                         )
                                      )

    @api.depends('invoice_ids')
    def _compute_invoices_count(self):
        for r in self:
            r.invoices_count = len(r.invoice_ids)

    @api.depends('invoice_line_ids.quantity', 'invoice_line_ids.price_unit')
    def _compute_invoiced_amount(self):
        for r in self:
            invoiced_amount = 0.0
            for invoice_line_id in r.invoice_line_ids:
                invoiced_amount += invoice_line_id.quantity * invoice_line_id.price_unit
            r.invoiced_amount = invoiced_amount

    @api.depends('amount', 'invoiced_amount')
    def _compute_to_invoice_amount(self):
        for r in self:
            r.to_invoice_amount = r.amount - r.invoiced_amount

    @api.depends('to_invoice_amount')
    def _compute_fully_invoiced(self):
        for r in self:
            r.fully_invoiced = True if float_is_zero(r.to_invoice_amount, precision_rounding=r.currency_id.rounding) and r.state not in ('draft', 'cancel') else False

    def _get_financial_fiscal_position(self):
        return self.order_id.partner_id.property_account_position_id

    def _get_interest_account(self):
        raise ValidationError(_("The method `_get_interest_account` has not been implemented for the model '%s'") % (self._name,))

    def _prepare_inv_line_data(self, qty=1, raise_if_fully_invoiced=False):
        """
        :param qty: float quantity to invoice
        """
        self.ensure_one()
        if self.fully_invoiced and raise_if_fully_invoiced:
            raise UserError(_("The interest '%s' has been fully invoiced already"))

        account = self._get_interest_account()

        res = {
            'name': self.name,
            'account_id': account.id,
            'price_unit': self.to_invoice_amount,
            'quantity': qty,
            'product_uom_id': self.order_id.product_id.uom_id.id,
            'product_id': self.order_id.product_id.id or False,
            'tax_ids': [(6, 0, self.order_id.tax_ids.ids)],
            'analytic_account_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.order_id.analytic_tag_ids.ids)],
        }
        if self._name == 'loan.borrow.interest.line':
            res['loan_borrow_interest_line_id'] = self.id
        elif self._name == 'loan.lend.interest.line':
            res['loan_lend_interest_line_id'] = self.id

        return res

    @api.constrains('rate_type_id', 'rate_line_id')
    def _check_rate_line_vs_date_type(self):
        for r in self:
            if r.rate_type_id:
                if r.rate_line_id:
                    if r.rate_type_id.type != 'floating':
                        raise ValidationError(_("Rate type '%s' is not a floating rate type. The interest line should not associate with a"
                                                " floating rate line."))

    @api.depends('date_to', 'order_id.interest_rate_type_id', 'order_id.expiry_interest_rate_type_id')
    def _get_rate_type(self):
        for r in self:
            if r.date_to and r.order_id.date_end:
                if r.date_to <= r.order_id.date_end:
                    r.rate_type_id = r.order_id.interest_rate_type_id
                else:
                    r.rate_type_id = r.order_id.expiry_interest_rate_type_id

    def _set_rate_type(self):
        pass

    @api.depends('date_from', 'date_to', 'rate_type_id')
    def _compute_nbr_of_days(self):
        ToBase = self.env['to.base']

        def is_full_month(nbr_of_days, date):
            return True if nbr_of_days == ToBase.get_days_of_month_from_date(date) else False

        for r in self:
            if not r.date_from or not r.date_to or not r.rate_type_id:
                r.nbr_of_days = 0
            else:
                date_to = r.date_to
                date_from = r.date_from
                nbr_of_days = ToBase.get_days_between_dates(date_from, date_to) + 1
                days_of_years = r.rate_type_id.get_days_of_year(date_from.year)
                days_of_month = r.rate_type_id.get_days_of_month(dt=date_from)
                if nbr_of_days > days_of_years:
                    nbr_of_days = days_of_years
                elif nbr_of_days > days_of_month or is_full_month(nbr_of_days, date_from):
                    nbr_of_days = days_of_month
                r.nbr_of_days = nbr_of_days

    @api.depends('loan_amount', 'daily_rate', 'nbr_of_days')
    def _compute_amount(self):
        for r in self:
            r.amount = r.daily_rate * r.nbr_of_days * r.loan_amount / 100

    @api.depends('date_from', 'date_to', 'rate_type_id')
    def _get_rate_line_id(self):
        for r in self:
            r.rate_line_id = False
            if not r.rate_type_id:
                continue
            rate_data = r.rate_type_id.get_rates(r.date_from, r.date_to)
            if isinstance(rate_data, float):
                continue
            if rate_data:
                r.rate_line_id = rate_data[0] 

    def _set_rate_line_id(self):
        pass

    def _get_invoicing_wizard_action_xml_id(self):
        raise ValidationError(_("The method `_get_invoicing_wizard_action()` has not been implemented for the model '%s'") % (self._name))

    def action_cancel(self):
        for r in self:
            if r.state == 'paid':
                if any(inv.state == 'paid' for inv in r.invoice_ids):
                    raise UserError(_("You must reset all the related invoices to the Open state before you can cancel the Loan Interest."))
            if r.state not in ('confirmed', 'paid'):
                raise UserError(_("You may be able to cancel a Loan Interest which is either in Confirmed or Paid state only"))
        self.write({'state': 'cancelled'})

    def action_invoice(self):
        interest_line_ids = self.filtered(lambda l: not l.fully_invoiced)
        if not interest_line_ids:
            raise UserError(_("No interest found for invoicing. If you have draft interests available, please confirm them before you can invoice them.\n"
                              "Tips: massively confirmation action is available at Interest list views..."))
        action = self.env.ref(self._get_invoicing_wizard_action_xml_id()).read()[0]
        action['context'] = {'default_interest_line_ids':interest_line_ids.ids}
        return action

    def action_view_invoices(self):
        invoice_ids = self.mapped('invoice_ids')
        action = self.env.ref(self._get_invoice_action_xml_id()).read()[0]
        if len(invoice_ids) > 1:
            action['domain'] = [('id', 'in', invoice_ids.ids)]
        elif len(invoice_ids) == 1:
            res = self.env.ref(self._get_invoice_form_view_xml_id(), False)
            action['views'] = [(res and res.id or False, 'form')]
            action['res_id'] = invoice_ids.ids[0]
        return action

    def action_confirm(self):
        for r in self:
            if r.disbursement_id.state not in ('paid', 'refunded'):
                raise ValidationError(_("You may not be able to confirm an interest if its associated disbursement is neither in Paid state nor in Refunded state."))
            if r.order_id.state != 'confirmed':
                raise UserError(_("You may not be able to confirm the interest '%s' while its contract (Ref.: %s) is not in"
                                  " Confirmed state.") % (r.name, r.order_id.name))
        super(AbstractLoanInterest, self).action_confirm()

    @api.depends('invoice_line_ids', 'invoice_line_ids.move_id')
    def _compute_invoices(self):
        for r in self:
            r.invoice_ids = r.invoice_line_ids.mapped('move_id')

    @api.depends('date_from', 'date_to', 'rate_type_id', 'rate_line_id', 'order_id.interest_cycle')
    def _compute_daily_rate(self):
        for r in self:
            if not r.rate_type_id or not r.date_from or not r.date_to:
                continue

            # get rate
            rate = 0.0
            if r.rate_type_id.type == 'flat':
                rate = r.rate_type_id.flat_rate
            elif r.rate_type_id.type == 'floating' and r.rate_line_id:
                rate = r.rate_line_id.rate

            # compute daily rate
            dt = r.date_from
            r.daily_rate = r.rate_type_id._calculate_daily_rate(rate, dt, r.order_id.interest_cycle)

    def _get_sequence(self):
        raise ValidationError(_("The method `_get_sequence()` has not been implemented for the model '%s' yet!") % (self._name,))

    def _prepare_payment_match_data(self, payment_id, matched_amount):
        data = super(AbstractLoanInterest, self)._prepare_payment_match_data(payment_id, matched_amount)
        data.update({
            'interest_id': self.id,
            })
        return data

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self._get_sequence() or '/'
        return super(AbstractLoanInterest, self).create(vals_list)

    def generate_timeframe(self):
        """
        @rtype: list
        @return: a list of tuple of two datetime string. E.g. [(dt1, dt2),....,(dtn,dtm)]
        """
        timeframe = []
        for r in self:
            timeframe.append((r.date_from, r.date_to))
        return timeframe
    
    def _get_invoice_form_view_xml_id(self):
        return 'account.view_move_form'

