import ast
from datetime import datetime

from dateutil.relativedelta import relativedelta
from dateutil import rrule

from odoo import models, fields, api, _
from odoo.tools import float_round, format_date
from odoo.exceptions import ValidationError, UserError


class AbstractLoanOrder(models.AbstractModel):
    _name = 'abstract.loan.order'
    _description = 'Abstract Loan Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_confirmed desc, date_end desc, id desc'

    def _get_default_product(self):
        return self.env['loan.interest.rate.type']._get_default_product()
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Canceled')], default='draft', string='Status', tracking=True, required=True, copy=False)

    name = fields.Char(string='Name',
                       required=True,
                       copy=False, readonly=True,
                       index=True, default='/')
    partner_id = fields.Many2one('res.partner', string='Loan Partner', required=True, readonly=True, states={'draft': [('readonly', False)]})

    # currency_id = fields.Many2one('res.currency', readonly=True, states={'draft': [('readonly', False)]}, compute='_compute_currency', store=True, required=True)

    currency_id = fields.Many2one('res.currency', readonly=True, states={'draft': [('readonly', False)]}, store=True, required=True)
    # loan_amount = fields.Monetary(string='Loan Amount', compute='_get_loan_amount', store=True,
    #                               required=True, readonly=False, states={'draft': [('readonly', False)]})
    loan_amount = fields.Monetary(string='Loan Amount', required=True)
    date_confirmed = fields.Date(string='Confirmation Date', default=fields.Date.today(), required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 copy=False,
                                 help='The date on which this order to be confirmed')
    date_end = fields.Date(string='Contract End', tracking=True, required=True,compute='_compute_date_end', store=True, readonly=True, states={'draft': [('readonly', False)]},
                           help="The date on which this contract will become expired")
    disbursement_method = fields.Selection([
        ('number', 'By Number'),
        ('end', 'By End Date'),
        ('upon_request', 'Upon Request')],
        string='Disbursement Method', default='number', required=True, readonly=True, states={'draft': [('readonly', False)]},
        help="How the loan amount is released\n"
        "- By Number: Loan amount will be divided into multiple Disbursements starting from the date specified in the field Disbursement Start."
        " The number of the installments depends on the input in the field Disbursements Number\n"
        "- By End Date: Loan amount will be divided into multiple Disbursement starting from the date specified in the field Disbursement Start Date"
        " and ending on the date specified in the field Disbursement End Date. The number of the Disbursements depends on the input in the field Disbursements"
        " Number.\n"
        "- Upon Request: Loan disbursement for a specific amount will be made manually by you.")
    disbursement_start_date = fields.Date(string='Start Date', compute='_get_disbursement_start_date', store=True,
                                          readonly=False, states={'confirmed': [('readonly', True)], 'done': [('readonly', True)], 'cancelled': [('readonly', True)]},
                                          help="The date on which the first disbursement of the loan is expected to be released")
    disbursement_method_number = fields.Integer(string='Disbursements Number', default=1,
                                                required=True, readonly=True, states={'draft': [('readonly', False)]},
                                                help='Disburses times in number')
    disbursement_method_period = fields.Integer(string='Period Months', default=1,
                                                required=True, readonly=True, states={'draft': [('readonly', False)]},
                                                help='Number of months between two disbursements')
    disbursement_end_date = fields.Date(string='End Date', readonly=True, states={'draft': [('readonly', False)]},
                                          help="In case the disbursement method is \"By End Date\", the last disbursement will be made on this day")

    principal_refund_method = fields.Selection([
        ('end_contract', 'By End of contract'),
        ('number', 'By Number')],
        string='Refund Method', default='end_contract',
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        help="Method to refund principal:\n"
        "By Number: Principal is splitted for multiple times of refund.\n"
        "By End of contract: refund all at one in the end of the contract")

    principal_refund_start_date = fields.Date(string='Refund Start Date', compute='_compute_principal_refund_start_date', store=True, readonly=False)

    principal_refund_method_number = fields.Integer(string='Refund Numbers', default=1,
                                                    required=True, readonly=True, states={'draft': [('readonly', False)]},
                                                    help='')
    principal_refund_method_period = fields.Integer(string='Period Months', default=1, required=True, readonly=True, states={'draft': [('readonly', False)]})
    interest_rate_type_id = fields.Many2one('loan.interest.rate.type', string='Interest Rate Type', required=True,
                                            readonly=True, states={'draft': [('readonly', False)]},
                                            help="The standard interest rate type which is applied during valid loan duration")
    expiry_interest_rate_type_id = fields.Many2one('loan.interest.rate.type', string='Expired Loan\'s Interest Rate Type', required=True,
                                                   readonly=True, states={'draft': [('readonly', False)]},
                                                   compute='_compute_expiry_interest_rate_type', store=True,
                                                   help="The interest rate type that will be applied after the loan is expired")
    product_id = fields.Many2one('product.product', string='Interest Product', domain="[('is_loan','=',True)]",
                                 default=_get_default_product,
                                 readonly=True, states={'draft': [('readonly', False)]},
                                 compute='_compute_product', store=True,
                                 tracking=True, required=True, help="The product that presents Loan Service for interests invoicing.")
    interest_cycle = fields.Selection([
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('biannually', 'Biannually'),
        ('annually', 'Annually')], string='Interest Cycle',
        default='monthly', required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        help="The period for interest calculation of the loan contract.\n"
        "- Weekly: each interest amount will be calculated for the period of seven days, starting from the day of week specified in the field 'Period Start Day'\n"
        "- Monthly: each interest amount will be calculated for the period of a full month, starting from the day of month specified in the field 'Period Start Day'\n"
        "- Quarterly: each interest amount will be calculated for the period of a quarter, starting from the day of quarter specified in the field 'Period Start Day'\n"
        "- Biannually: each interest amount will be calculated for the period of six months, starting from the day of the six-month period specified in the field 'Period Start Day'\n"
        "- Annually: each interest amount will be calculated for the period of a full year, starting from the day of year specified in the field 'Period Start Day'\n")
    interest_period_start_day = fields.Integer(string='Period Start Day', default=1, required=True,
                                               readonly=True, states={'draft': [('readonly', False)]},
                                               help="The start day of the interest cycle from which the interest calculation will be counted. The default"
                                               " value is 1 which means that the cycle is standard (i.e. weeks start from Monday, Months start from 1st day of month,"
                                               " Quarters start from 1st of Jan/Apr/Jul/Oct, Biannuals start from 1st of Jan/Jul, Anmuals start from 1st of Jan. Here"
                                               " is further explanation:\n"
                                               "- Weekly Cycle: 1~7 for Monday~Sunday (Weeks start with Monday)\n"
                                               "- Monthly Cycle: 1~28 for day 1~28 of the month\n"
                                               "- Quarterly Cycle: 1~89 for day 1~89 of the quarter\n"
                                               "- Biannually Cycle: 1~180 for day 1~180 of the biannual\n"
                                               "- Annually Cycle: 1~360 for day 1~360 of the year\n"
                                                )
    interest_incl_disburment_date = fields.Boolean(string="Include Disbursement Date", default=False,
                                                   readonly=True, states={'draft': [('readonly', False)]},
                                                   help="If checked, interest computation"
                                                   " includes the date on which the disbursment is made. Otherwise, the computation start"
                                                   " from the following day.")
    interest_incl_refund_date = fields.Boolean(string="Include Refund Date", default=True,
                                               readonly=True, states={'draft': [('readonly', False)]},
                                               help="If checked, the interest computation includes the loan refund date. Otherwise,"
                                               " it counts to the day before only.")

    payment_term_id = fields.Many2one('account.payment.term', string='Interest Payment Terms')
    due_day = fields.Integer(string='Due Day', default=0,
                             help="The due day of the interest counted from the last date of the interest cycle. Default value is zero,"
                             " meaning the due date is the same as the last date if the interest cycle.\n"
                             "- Positive value means the due date of the interest is later than the last date of the interest cycle;\n"
                             "- Negative value means the due date is earlier than the last date of the interest cycle.\n")

    invoice_ids = fields.Many2many('account.move', string='Invoices', compute='_compute_invoices', store=True)
    invoices_count = fields.Integer(string='Invoices Count', compute='_compute_invoices_count', store=True)

    terms_conditions = fields.Html(string='Terms and Conditions')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True,
                                 readonly=True, states={'draft': [('readonly', False)]})
    loan_duration = fields.Integer(string='Loan Duration', default=12, required=True,
                                       readonly=True, states={'draft': [('readonly', False)]},
                                       help="The duration (in months) of the loan contract.")
    journal_id = fields.Many2one('account.journal', string='Journal',
                                          required=True, readonly=True, states={'draft': [('readonly', False)]})

    account_id = fields.Many2one('account.account', string='Loan Account',
                                          required=True, readonly=True, states={'draft':[('readonly', False)]})
    refund_lines_count = fields.Integer(string='Disbursements Count')
    received_amount = fields.Monetary(string='Received', compute='_compute_received_amount', store=True, copy=False,
                                      help="Loan Amount that you have received")
    to_receive_amount = fields.Monetary(string='To-Receive', compute='_compute_to_receive_amount', store=True, copy=False,
                                      help="Loan Amount that have not been transfered to you yet.")
    refunded_amount = fields.Monetary(string='Refunded', compute='_compute_refunded_amount', store=True, copy=False,
                                      help="Loan Amount (aka principal) that you have refunded")

    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)
    tax_ids = fields.Many2many('account.tax', string='Taxes', help="The taxes which will be applied during invoicing loan interests of the contract")
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', help="If specified, when invoicing interests of this contract,"
                                          " this analytic account will be filled automatically into the invoice lines")
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', default=lambda self: self._get_default_analytic_tags(),
                                        help="If specified, when invoicing interests of this contract,"
                                        " these analytic tags will be filled automatically into the invoice lines")

    object_cost_id = fields.Many2one('object.cost', string='Object Cost', ondelete='cascade')
    part_id = fields.Many2one('res.partner', string='Partner')

    moves_count = fields.Integer(string='Journal Entries Count', compute='_compute_moves_count', copy=False)
    invoice_state = fields.Selection([
        ('nothing_to_invoice', 'Nothing To Invoice'),
        ('to_invoice', 'To Invoice'),
        ('fully_invoiced', 'Fully Invoiced')], string='Invoice Status', compute='_compute_invoice_status', store=True)
    loan_number = fields.Char(string="Number")

    _sql_constraints = [
        # ('loan_amount_positive_check',
        #  'CHECK(loan_amount > 0.0 and state != "draft")',
        #  "Zero Loan Amount makes no sense. It must be greater than zero!"),
        ('loan_duration_positive_check',
         'CHECK(loan_duration > 0.0)',
         "Loan Duration must be greater than zero!"),
        ('disbursement_method_period_check',
         'CHECK(disbursement_method_period >= 0.0)',
         "Period Months must be greater than or equal to zero!"),
        ('interest_period_start_day_positive_check',
         'CHECK(interest_period_start_day > 0)',
         "The Period Start Day must be greater than zero!"),
    ]
    
    @api.constrains('disbursement_start_date', 'date_confirmed')
    def _check_order_date(self):
        for r in self:
            if r.disbursement_start_date < r.date_confirmed:
                raise ValidationError(_("Disbursement start date: %s cannot be smaller Contract confirm date: %s")%(r.disbursement_start_date,r.date_confirmed))

    @api.model
    def _get_default_analytic_tags(self):
        """
        For potential inheritance
        """
        return []

    @api.depends('state',
                 'interest_line_ids', 'interest_line_ids.fully_invoiced', 'interest_line_ids.state')
    def _compute_invoice_status(self):
        for r in self:
            if r.state in ('draft', 'cancelled'):
                r.invoice_state = 'nothing_to_invoice'
            elif r.state == 'done':
                r.invoice_state = 'fully_invoiced'
            else:
                interest_line_ids = r.interest_line_ids
                if all(line.fully_invoiced == True for line in interest_line_ids.filtered(lambda l: l.state != 'cancelled')):
                    invoice_state = 'fully_invoiced'
                elif any(line.state == 'confirmed' for line in interest_line_ids):
                    invoice_state = 'to_invoice'
                else:
                    invoice_state = 'nothing_to_invoice'

                r.invoice_state = invoice_state

    # @api.depends('disbursement_line_ids.amount')
    # def _get_loan_amount(self):
    #     for r in self:
    #         r.loan_amount = sum(r.disbursement_line_ids.mapped('amount'))

    def _get_move_ids(self):
        return self.disbursement_line_ids.mapped('move_ids') + self.refund_line_ids.mapped('move_ids')

    def _compute_moves_count(self):
        for r in self:
            r.moves_count = len(r._get_move_ids())

    def action_view_moves(self):
        self.ensure_one()
        move_ids = self._get_move_ids()
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

    def open_reconcile_view(self):
        move_ids = self._get_move_ids()
        return move_ids.mapped('line_ids').open_reconcile_view()

    @api.constrains('principal_refund_start_date')
    def _check_principal_refund_start_date(self):
        for r in self:
            first_disbursement_date = r.get_first_disbursement_date()
            if r.principal_refund_start_date < first_disbursement_date:
                raise ValidationError(_("The First refund (%s) must not be earlier than the first disbursement (%s)")
                                      % (format_date(r.env, r.principal_refund_start_date), format_date(r.env, first_disbursement_date)),)

    @api.constrains('company_id', 'product_id')
    def _check_company_vs_product(self):
        for r in self:
            if r.product_id.company_id and r.product_id.company_id.id != r.company_id.id:
                raise ValidationError(_("The product '%s' seems to not belong to the company %s") % (r.product_id.display_name, r.company_id.name))

    def _check_company_vs_journal(self):
        for r in self:
            if r.journal_id and r.journal_id.company_id.id != r.company_id.id:
                raise ValidationError(_("The journal '%s' seems to not belong to the company %s") % (r.journal_id.display_name, r.company_id.name))

    def _check_company_vs_account(self):
        for r in self:
            if r.account_id and r.account_id.company_id.id != r.company_id.id:
                raise ValidationError(_("The account '%s' seems to not belong to the company %s") % (r.account_id.display_name, r.company_id.name))


    @api.depends('disbursement_line_ids.paid_amount')
    def _compute_received_amount(self):
        for r in self:
            received_amount = 0.0
            for line in r.disbursement_line_ids:
                if line.state != 'cancelled' and line.paid_amount != 0:
                    received_amount += line.paid_amount
            r.received_amount = received_amount

    @api.depends('received_amount', 'loan_amount')
    def _compute_to_receive_amount(self):
        for r in self:
            r.to_receive_amount = r.loan_amount - r.received_amount

    @api.depends('refund_line_ids.paid_amount')
    def _compute_refunded_amount(self):
        for r in self:
            r.refunded_amount = sum(r.refund_line_ids.mapped('paid_amount'))

    @api.constrains('interest_cycle', 'interest_period_start_day')
    def _check_interest_cycle(self):
        for r in self:
            if r.interest_cycle == 'weekly':
                day_range = list(range(1, 8))
                if r.interest_period_start_day not in day_range:
                    raise UserError(_("Period Start Day must be 1~7 for Weekly term"))

            if r.interest_cycle == 'monthly':
                day_range = list(range(1, 29))
                if r.interest_period_start_day not in day_range:
                    raise UserError(_("Period Start Day must be 1~28 for Monthly term"))

            if r.interest_cycle == 'quarterly':
                day_range = list(range(1, 90))
                if r.interest_period_start_day not in day_range:
                    raise UserError(_("Period Start Day must be 1~89 for Quarterly term"))

            if r.interest_cycle == 'biannually':
                day_range = list(range(1, 181))
                if r.interest_period_start_day not in day_range:
                    raise UserError(_("Period Start Day must be 1~180 for Biannually term"))

            if r.interest_cycle == 'annually':
                day_range = list(range(1, 361))
                if r.interest_period_start_day not in day_range:
                    raise UserError(_("Period Start Day must be 1~360 for Annually term"))

    @api.constrains('principal_refund_method', 'principal_refund_method_number')
    def _check_principal_refund_method_vs_principal_refund_method_number(self):
        for r in self:
            if r.principal_refund_method == 'number' and not r.principal_refund_method_number > 0:
                raise UserError(_("The Refund Numbers must be greater than zero while the Refund Method is set as 'By Number'."))

    @api.constrains('principal_refund_method', 'principal_refund_method_number', 'principal_refund_method_period')
    def _check_principal_refund_method_vs_principal_refund_method_number_vs_principal_refund_method_period(self):
        for r in self:
            if r.principal_refund_method == 'number' and r.principal_refund_method_number > 1 and not r.principal_refund_method_period > 0:
                raise UserError(_("Period Months for must be greater than 0 (zero) while the Refund Method is set as 'By Number'"
                                  " and the Refund Numbers is greater than 1 (one)."))

    @api.constrains('disbursement_method_period', 'disbursement_method_number')
    def _check_disbursement_method_period_vs_disbursement_method_number(self):
        for r in self:
            if r.disbursement_method_number > 1 and not r.disbursement_method_period > 0:
                raise UserError(_("Disbursement Period Months must be greater than Zero (0) while Disbursements Number is greater than One (1)."))

    @api.constrains('disbursement_method', 'disbursement_method_number')
    def _check_disbursement_method_vs_disbursement_method_number(self):
        for r in self:
            if r.disbursement_method == 'number' and not r.disbursement_method_number > 0:
                raise UserError(_("When choosing 'By Number' as the Disbursement Method, the Disbursements Number must be greater than Zero"))

    @api.depends('interest_line_ids', 'interest_line_ids.invoice_ids')
    def _compute_invoices(self):
        for r in self:
            r.invoice_ids = r.interest_line_ids.mapped('invoice_ids')

    @api.depends('invoice_ids')
    def _compute_invoices_count(self):
        for r in self:
            r.invoices_count = len(r.invoice_ids)

    def get_first_disbursement_date(self):
        if self.disbursement_line_ids:
            return self.disbursement_line_ids[0].date or self.disbursement_start_date
        else:
            return self.disbursement_start_date

    @api.onchange('journal_id', 'company_id')
    def _onchage_currency_jn(self):
        for r in self:
            if not self.currency_id:
                if r.journal_id and r.journal_id.currency_id:
                    r.currency_id = r.journal_id.currency_id
                elif r.company_id:
                    r.currency_id = r.company_id.currency_id
                else:
                    r.currency_id = self.env.company.currency_id

    @api.depends(
        'disbursement_end_date',
        'disbursement_method',
        'disbursement_method_number',
        'disbursement_method_period',
        'date_confirmed'
        )
    def _get_disbursement_start_date(self):
        for r in self:
            disbursement_start_date = False
            if r.disbursement_method == 'number':
                disbursement_start_date = r.date_confirmed
            elif self.disbursement_method == 'end':
                if r.disbursement_method_number == 1:
                    disbursement_start_date = r.disbursement_end_date
                elif r.disbursement_method_number > 1:
                    disbursement_end_dt = r.disbursement_end_date
                    if disbursement_end_dt:
                        disbursement_start_dt = disbursement_end_dt - relativedelta(months=self.disbursement_method_number * self.disbursement_method_period - 1)
                        disbursement_start_date = disbursement_start_dt
            else:
                disbursement_start_date = r.date_confirmed
            r.disbursement_start_date = disbursement_start_date
    
    @api.depends('disbursement_start_date','loan_duration')
    def _compute_date_end(self):
        for r in self:
            if r.disbursement_start_date and r.loan_duration:
                r.date_end = r.disbursement_start_date + relativedelta(months=+r.loan_duration)
    
    @api.depends(
        'principal_refund_method',
        'principal_refund_method_number',
        'principal_refund_method_period',
        'date_end')
    def _compute_principal_refund_start_date(self):
        for r in self:
            if r.principal_refund_method == 'end_contract':
                r.principal_refund_start_date = r.date_end
            elif r.principal_refund_method == 'number':
                if r.principal_refund_method_number == 1:
                    r.principal_refund_start_date = r.date_end
                elif r.principal_refund_method_number > 1:
                    principal_refund_start_date = r.date_end - relativedelta(months=r.principal_refund_method_number * r.principal_refund_method_period)
                    first_disbursement_date = r.get_first_disbursement_date()
                    if first_disbursement_date and not principal_refund_start_date < first_disbursement_date:
                        r.principal_refund_start_date = principal_refund_start_date

    @api.constrains('disbursement_start_date', 'principal_refund_start_date')
    def _check_disbursement_start_date_principal_refund_start_date(self):
        for r in self:
            if r.disbursement_start_date and r.principal_refund_start_date and r.principal_refund_start_date < r.disbursement_start_date:
                raise UserError(_("The First refund (%s) must not be earlier than the first disbursement (%s)")
                                % (format_date(r.env, fields.Date.to_string(r.principal_refund_start_date)), format_date(r.env, r.disbursement_start_date))
                                )

    @api.depends('interest_rate_type_id.product_id')
    def _compute_product(self):
        for r in self:
            r.product_id = r.interest_rate_type_id.product_id and r.interest_rate_type_id.product_id or False

    @api.depends('interest_rate_type_id')
    def _compute_expiry_interest_rate_type(self):
        for r in self:
            r.expiry_interest_rate_type_id = r.interest_rate_type_id and r.interest_rate_type_id.expiry_rate_type_id or r.interest_rate_type_id or False

    def action_compute_data_line(self):
        regenerate = self.env.context.get('regenerate', True)
        for r in self:
            if not regenerate and r.refund_line_ids and r.disbursement_line_ids:
                continue
            r.disbursement_line_ids.unlink()
            r.refund_line_ids.unlink()
            r.action_generate_disbursements()

    def action_invoice(self):
        interest_line_ids = self.mapped('interest_line_ids').filtered(lambda l: l.state == 'confirmed')
        if not interest_line_ids:
            raise UserError(_("No interest found for invoicing. If you have draft interests available, please confirm them before you can invoice them.\n"
                              "Tips: massively confirmation action is available at Interest list views..."))

        action = self.env.ref(self._get_invoicing_wizard_action_xml_id()).read()[0]
        action['context'] = {'default_interest_line_ids':interest_line_ids.ids}
        return action

    def action_confirm(self):
        for r in self:
            if r.state != 'draft':
                raise UserError(_("You may not be able to confirm the order '%s' while its status is not Draft") % (r.name,))
        self.with_context(regenerate=False).action_compute_data_line()
        self.write({'state': 'confirmed'})
        self.mapped('disbursement_line_ids').action_confirm()

    def action_done(self):
        for r in self:
            if r.state != 'confirmed':
                raise UserError(_("You may not be able to set the order '%s' as Done while its status is not Confirmed") % (r.name,))
            if any(line.state == 'confirmed' for line in r.disbursement_line_ids):
                raise UserError(_("You may not be able to mark the Loan Contract %s as Done while it still has a confirmed disbursement."
                                  " You may need to remove or cancel it to proceed.") % (r.name,))
            if any(line.state == 'confirmed' for line in r.refund_line_ids):
                raise UserError(_("You may not be able to mark the Loan Contract %s as Done while it still has a confirmed refund."
                                  " You may need to remove or cancel it to proceed.") % (r.name,))
            if any(line.state == 'confirmed' for line in r.interest_line_ids):
                raise UserError(_("You may not be able to mark the Loan Contract %s as Done while it still has a confirmed loan interest."
                                  " You may need to remove or cancel it to proceed.") % (r.name,))

            for inv in r.invoice_ids:
                if inv.state != 'posted':
                    raise ValidationError(_("You may not be able to mark the Loan Contract %s as Done while the invoice %s is not in Posted state.")
                                           % (r.name, inv.name))

        self.mapped('interest_line_ids').filtered(lambda l: l.state not in ('confirmed', 'paid', 'cancelled')).unlink()
        self.write({'state': 'done'})

    def action_draft(self):
        for r in self:
            if r.state != 'cancelled':
                raise UserError(_("You may not be able to cancel the order ' %s' while its status is not Cancelled") % (r.name,))
        self.mapped('disbursement_line_ids').action_draft()
        self.write({'state': 'draft'})

    def action_cancel(self):
        for r in self:
            if r.disbursement_payment_match_ids:
                raise UserError(_("You may not be able to cancel the contract '%s' while there has been a disbursement made to it.")
                                % (r.name,))
        self.mapped('disbursement_line_ids').action_cancel()
        self.mapped('refund_line_ids').unlink()
        self.mapped('interest_line_ids').unlink()
        self.write({'state': 'cancelled'})

    def _get_disbursement_model(self):
        raise ValidationError(_("The method `_get_disbursement_model` has not been implemented for the model '%s' yet") % (self._name,))

    def _prepare_disbursement_line_data(self, amount, date_start, date_maturity,disbursement_start_date,loan_duration):
        return {
            'order_id': self.id,
            'amount': amount,
            'date': date_start,
            'date_maturity': date_maturity,
            'date_start': disbursement_start_date,
            'loan_duration': loan_duration,
            }

    def action_generate_disbursements(self):
        loan_amount = self.loan_amount
        if not self.env.context.get('regenerate', True):
            self.mapped('disbursement_line_ids').filtered(lambda l: l.state == 'draft').unlink()
        for r in self:
            vals_list = []
            existing_disbursement_line_ids = r.disbursement_line_ids.filtered(lambda l: l.state != 'draft')
            amount = loan_amount - sum(existing_disbursement_line_ids.mapped('amount'))
            if r.disbursement_method in ('number', 'end'):
                if r.disbursement_method_number > 0:
                    amount = float_round(amount / r.disbursement_method_number, precision_rounding=r.currency_id.rounding)
                    date_start = r.get_first_disbursement_date()
                    for i in range(r.disbursement_method_number):
                        if date_start in existing_disbursement_line_ids.mapped('date'):
                            continue
                        # lass disbursement
                        if i == r.disbursement_method_number - 1:
                            amount = loan_amount - (r.disbursement_method_number - 1) * amount
                        vals_list.append(r._prepare_disbursement_line_data(amount, date_start, date_start, r.disbursement_start_date, r.loan_duration))
                        new_date_start = date_start + relativedelta(months=r.disbursement_method_period)
                        date_start = new_date_start
            disbursement_line_ids = self.env[self._get_disbursement_model()].create(vals_list)
            disbursement_line_ids.action_generate_refund_lines()

    def _prepare_refund_data(self, amount=None, date=None, date_maturity=None):
        disbursement_ids = self.disbursement_line_ids

        date = date or self.date_end
        date_maturity = date_maturity or self.date_end
        data = {
            'order_id': self.id,
            'date': date,
            'date_maturity': date_maturity,
            'disbursement_ids': [(6, 0, disbursement_ids.ids)]
            }
        if amount:
            data['amount'] = amount
        return data

    def _get_rrule_freq(self):
        interest_cycle = self.interest_cycle
        if interest_cycle == 'weekly':
            freq = rrule.WEEKLY
        elif interest_cycle == 'monthly':
            freq = rrule.MONTHLY
        elif interest_cycle == 'annually':
            freq = rrule.YEARLY
        else:
            raise ValidationError(_("Interest Payment Recurrent '%s' is not supported.") % (interest_cycle,))
        return freq

    def find_last_date_of_period(self, date):
        """
        @rtype: date object
        @return: The last date of the given date's period
        """
        if self.interest_period_start_day == 1:
            dt = self.env['to.base'].find_last_date_of_period(self.interest_cycle, date)
        else:
            dt = self.env['to.base'].find_last_date_of_period(self.interest_cycle, date, date_is_start_date=True)
        if isinstance(dt, datetime):
            dt = dt.date()
        return dt

    def _get_invoice_action_xml_id(self):
        raise ValidationError(_("The method `_get_invoice_action_xml_id()` has not been implemented for the model '%s' yet") % (self._name,))

    def _get_invoice_form_view_xml_id(self):
        return 'account.view_move_form'

    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref(self._get_invoice_action_xml_id()).read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            res = self.env.ref(self._get_invoice_form_view_xml_id(), False)
            action['views'] = [(res and res.id or False, 'form')]
            action['res_id'] = invoices.ids[0]

        return action

    def _get_refund_line_action_xml_id(self):
        raise ValidationError(_("The method `_get_refund_line_action_xml_id()` has not been implemented for the model '%s' yet") % (self._name,))

    def _get_refund_line_form_view_xml_id(self):
        raise ValidationError(_("The method `_get_refund_line_action_xml_id()` has not been implemented for the model '%s' yet") % (self._name,))

    def action_view_refund_lines(self):
        disbursement_line_ids = self.mapped('refund_line_ids')
        action = self.env.ref(self._get_refund_line_action_xml_id()).read()[0]
        if len(disbursement_line_ids) > 1:
            action['domain'] = [('id', 'in', disbursement_line_ids.ids)]
        elif len(disbursement_line_ids) == 1:
            res = self.env.ref(self._get_refund_line_form_view_xml_id(), False)
            action['views'] = [(res and res.id or False, 'form')]
            action['res_id'] = disbursement_line_ids.ids[0]

        return action

    def _get_interest_line_action_xml_id(self):
        raise ValidationError(_("The method `_get_interest_line_action_xml_id()` has not been implemented for the model '%s' yet") % (self._name,))

    def _get_interest_line_form_view_xml_id(self):
        raise ValidationError(_("The method `_get_interest_line_form_view_xml_id()` has not been implemented for the model '%s' yet") % (self._name,))

    def action_view_interest_lines(self):
        interest_line_ids = self.mapped('interest_line_ids')
        action = self.env.ref(self._get_interest_line_action_xml_id()).read()[0]
        if len(interest_line_ids) > 1:
            action['domain'] = [('id', 'in', interest_line_ids.ids)]
        elif len(interest_line_ids) == 1:
            res = self.env.ref(self._get_interest_line_form_view_xml_id(), False)
            action['views'] = [(res and res.id or False, 'form')]
            action['res_id'] = interest_line_ids.ids[0]

        return action

    def _get_disbursement_payment_action_xml_id(self):
        raise ValidationError(_("The method `_get_disbursement_payment_action_xml_id()` has not been implemented for the model '%s' yet") % (self._name,))

    def action_disbursement_register_wizard(self):
        disbursement_ids = self.mapped('disbursement_line_ids').filtered(lambda l:l.state == 'confirmed')
        action = self.env.ref(self._get_disbursement_payment_action_xml_id()).read()[0]
        ctx = ast.literal_eval(action['context'])
        ctx.update({'default_disbursement_ids': disbursement_ids.ids,'default_order_id': self.id})
        action['context'] = ctx
        return action

    def unlink(self):
        self.mapped('disbursement_line_ids').unlink()
        return super(AbstractLoanOrder, self).unlink()

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        default['journal_id'] = self.journal_id.id
        default['account_id'] = self.account_id.id
        return super(AbstractLoanOrder, self).copy(default=default)

    @api.model
    def create(self, vals):
        res = super(AbstractLoanOrder, self).create(vals)
        res._check_company_vs_journal()
        res._check_company_vs_account()
        return res

    def write(self, vals):
        res = super(AbstractLoanOrder, self).write(vals)
        account_id = vals.get('account_id', False)
        if account_id:
            for r in self:
                r._check_company_vs_account()

        journal_id = vals.get('journal_id', False)
        if journal_id:
            for r in self:
                r._check_company_vs_journal()
        return res

