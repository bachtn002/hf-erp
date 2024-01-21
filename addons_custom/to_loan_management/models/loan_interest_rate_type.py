from dateutil import rrule

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LoanInterestRateType(models.Model):
    _name = 'loan.interest.rate.type'
    _inherit = 'mail.thread'
    _description = 'Interest Rate Type'

    # @api.model
    def _get_default_product(self):
        return self.env.ref('to_loan_management.service_loan', raise_if_not_found=False)

    name = fields.Char(string='Name', translate=True, help="Optional name of the interest rate type")
    type = fields.Selection([
        ('flat', 'Flat Rate'),
        ('floating', 'Floating Rate')],
        string='Type', required=True, help='Type of rate')
    flat_rate = fields.Float(string='Flat Rate (%)', help='Flat Rate for this interest type (%)')

    floating_rate_ids = fields.One2many('loan.floating.rate', 'interest_date_type_id', string='Floating Rates',)

    interest_rate_period = fields.Selection([
        ('week', 'Per Week'),
        ('month', 'Per Month'),
        ('year', 'Per Year')], string='Rate Period', default='year', required=True,
        help='The period that the interest rate is applied for rate computation')
    fixed_days_of_year = fields.Boolean(string='Fixed Days of Year', default=False, help="If checked, number of days"
                                        " of every year for this rate type will be the same as specified in the field Days of Years below")
    days_of_year = fields.Integer(string='Days of Year', default=365, help="If the 'Fixed Days of Year' is checked, number of days"
                                  " of every year will be the same as specified here")
    fixed_days_of_month = fields.Boolean(string='Fixed Days of Month', default=False, help="If checked, number of days of every month"
                                         " for this rate type will be the same as specified in the field Days of Month below")
    days_of_month = fields.Integer(string='Days of Month', default=30, help="If the 'Fixed Days of Month' is checked, number of days"
                                  " of every month will be the same as specified here")

    product_id = fields.Many2one('product.product', string='Product', domain="[('is_loan','=',True)]", tracking=True,
                                 default=_get_default_product,
                                 help="A service product that presents Loan Interest (for accounting integration purpose)")
    expiry_rate_type_id = fields.Many2one('loan.interest.rate.type', string='Expiry Rate Type', help="The rate type that will"
                                        " be applied to the loans of this type after loan contract ending.")

    def get_days_of_year(self, year=None):
        """
        Get number of days of a given years related to this rate type.
        """
        if self.fixed_days_of_year:
            return self.days_of_year
        else:
            TOBase = self.env['to.base']
            year = year or TOBase.split_date(fields.Date.today())[0]
            return TOBase.get_days_between_dates(fields.Date.from_string("%s-01-01" % year), fields.Date.from_string("%s-12-31" % year))

    def get_days_of_month(self, year=None, month=None, dt=None):
        if self.fixed_days_of_month:
            return self.days_of_month
        else:
            if year and month and dt:
                raise ValidationError(_("You may not pass year and month and dt at once to the method `get_days_of_month()`. You may either leave it empty"
                                        " or pass dt only or pass year and month only."))
            elif year and month:
                dt = fields.Date.from_string("%s-%s-01" % (year, month))
            elif not dt:
                dt = fields.Date.from_string(fields.Date.today())
            return self.env['to.base'].get_days_of_month_from_date(dt)

    def get_floating_rate_line(self, date):
        line_id = self.env['loan.floating.rate'].search([
            ('interest_date_type_id', '=', self.id),
            ('date_from', '<=', date),
            '|', ('date_to', '=', False), ('date_to', '>', date)], order='date_from desc', limit=1)
        return line_id

    def _calculate_daily_rate(self, rate, date, interest_cycle):
        """
        @param rate: the input rate to calculate daily rate
        @param date: date or datetime object
        @param interest_cycle: Interest Payment Recurrence which is either 'weekly' or 'monthly' or 'annually'         
        """
        if self.interest_rate_period == 'week':
            daily_rate = rate / 7
        elif self.interest_rate_period == 'month':
            daily_rate = rate / self.get_days_of_month(dt=date)
        elif self.interest_rate_period == 'year':
            if interest_cycle == 'monthly':
                daily_rate = (rate / 12) / self.get_days_of_month(dt=date)
            else:
                daily_rate = rate / self.get_days_of_year(date.year)
        else:
            raise ValidationError(_("The Rate Period '%s' is not supported!"))
        return daily_rate

    def get_daily_rates(self, date_start_str, date_end_str, interest_cycle):
        """
        Return daily rates that applied to the current interest rate type     
           
        @rtype: dict {
            datetime: {
                'rate': rate,
                'rate_line_id': rate_line_id
                }
            }
        """
        dtstart = fields.Date.from_string(date_start_str)
        until = fields.Date.from_string(date_end_str)
        res = {}
        for dt in rrule.rrule(rrule.DAILY, dtstart=dtstart, until=until):
            dt_str = fields.Date.to_string(dt)
            rate = None
            rate_line_id = None
            if self.type == 'flat':
                rate = self.flat_rate
            elif self.type == 'floating':
                rate_line_id = self.get_floating_rate_line(dt_str)
                if rate_line_id:
                    rate = rate_line_id.rate

            if rate is not None:
                rate = self._calculate_daily_rate(rate, dt, interest_cycle)
            else:
                rate = 0.0
            res[dt] = {
                'rate': rate,
                'rate_line_id': rate_line_id
                }
        return res

    def get_rates(self, date_start, date_end):
        if self.type == 'flat':
            return self.flat_rate
        elif self.type == 'floating':
            floating_line_ids = self.env['loan.floating.rate'].search([
                ('interest_date_type_id', '=', self.id),
                ('date_from', '<=', date_end),
                '|', ('date_to', '=', False), ('date_to', '>', date_start),
                ])
            return floating_line_ids

    def _get_display_name(self):
        interest_rate_period_label = dict(self._fields['interest_rate_period']._description_selection(self.env)).get(self.interest_rate_period)

        name = '%s ' % self.name if self.name else ''
        if self.type == 'flat':
            name = '%s%s %s %s' % (name, _("Flat Rate"), str(self.flat_rate) + '%', interest_rate_period_label)
        else:
            name = '%s%s' % (name, _("Floating Rate"))

        return name

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, rec._get_display_name()))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = [
                '|', '|',
                ('flat_rate', 'ilike', '%' + name + '%'),
                ('interest_rate_period', 'ilike', '%' + name + '%'),
                ('display_name', operator, name)]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()

