# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import copy
import ast

from odoo import models, fields, api, _
from odoo.tools import float_is_zero, ustr
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


class ReportAccountFinancialReport(models.Model):
    _inherit = "account.financial.html.report"
    _description = "Account Report (HTML)"

    display_code = fields.Boolean(string="Show Display Code", default=False)
    display_present = fields.Boolean(string="Show Present Code", default=False)

    def _get_columns_name(self, options):
        columns = super(ReportAccountFinancialReport, self)._get_columns_name(options)

        if self.display_code:
            columns.insert(1, {'name': _('Code'), 'class': 'number'})
        if self.display_present:
            columns.insert(2, {'name': _('Present'), 'class': 'number'})
        return columns

    filter_branch = True

    def open_journal_items(self, options, params):
        action = super(ReportAccountFinancialReport, self).open_journal_items(options, params)
        domain = action['domain']
        if options:
            if options.get('branch'):
                domain = expression.AND([domain, [
                    ('branch_id', 'in', [branch.get('id') for branch in options['branch'] if branch['selected']])]])

            action['domain'] = domain
        return action


class AccountFinancialReportLine(models.Model):
    _inherit = "account.financial.html.report.line"

    display_code = fields.Char(string="Display Code")
    display_present = fields.Char(string="Present Code")
    # hide_in_report = fields.Boolean(string='Hide In Report')
    groups_by = fields.Char('Groups By')

    def _format(self, value):
        if type(value['name']) == str:
            value['class'] = 'number text-muted'
            return value
        res = super(AccountFinancialReportLine, self)._format(value)
        return res

    @api.constrains('groups_by')
    def _check_same_journal_sum_group(self):
        for item in self:
            if item.groups_by:
                groups_by = item.groups_by.split(",")
                for group in groups_by:
                    if group and group not in self.env['account.move.line']:
                        raise ValidationError(_("Group by should be a journal item field"))

    def _compute_sum(self, options_list):
        ''' Compute the values to be used inside the formula for the current line.
        If called, it means the current line formula contains something making its line a leaf ('sum' or 'count_rows')
        for example.

        The results is something like:
        {
            'sum':          {key: <balance>...},
            'sum_if_pos':   {key: <balance>...},
            'sum_if_neg':   {key: <balance>...},
            'count_rows':   {period_index: <number_of_rows_in_period>...},
        }

        ... where:
        'period_index' is the number of the period, 0 being the current one, others being comparisons.

        'key' is a composite key containing the period_index and the additional group by enabled on the financial report.
        For example, suppose a group by 'partner_id':

        The keys could be something like (0,1), (1,2), (1,3), meaning:
        * (0,1): At the period 0, the results for 'partner_id = 1' are...
        * (1,2): At the period 1 (first comparison), the results for 'partner_id = 2' are...
        * (1,3): At the period 1 (first comparison), the results for 'partner_id = 3' are...

        :param options_list:        The report options list, first one being the current dates range, others being the
                                    comparisons.
        :return:                    A python dictionary.
        '''
        self.ensure_one()
        params = []
        queries = []

        AccountFinancialReportHtml = self.financial_report_id
        if self.groupby:
            groupby_list = [self.groupby] + AccountFinancialReportHtml._get_options_groupby_fields(options_list[0])
        else:
            groupby_list = AccountFinancialReportHtml._get_options_groupby_fields(options_list[0])
        groupby_clause = ','.join('account_move_line.%s' % gb for gb in groupby_list)
        ct_query = self.env['res.currency']._get_query_currency_table(options_list[0])
        financial_report = self._get_financial_report()

        # Prepare a query by period as the date is different for each comparison.

        for i, options in enumerate(options_list):
            new_options = self._get_options_financial_line(options)
            line_domain = self._get_domain(new_options, financial_report)

            tables, where_clause, where_params = AccountFinancialReportHtml._query_get(new_options, domain=line_domain)

            queries.append('''
                SELECT
                    ''' + (groupby_clause and '%s,' % groupby_clause) + '''
                    %s AS period_index,
                    COUNT(DISTINCT account_move_line.''' + (self.groupby or 'id') + ''') AS count_rows,
                    COALESCE(SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)), 0.0) AS balance
                FROM ''' + tables + '''
                JOIN ''' + ct_query + ''' ON currency_table.company_id = account_move_line.company_id
                WHERE ''' + where_clause + '''
                ''' + (groupby_clause and 'GROUP BY %s' % groupby_clause) + '''
            ''')
            params.append(i)
            params += where_params

        # Fetch the results.

        results = {
            'sum': {},
            'sum_if_pos': {},
            'sum_if_neg': {},
            'count_rows': {},
        }

        financial_report._cr_execute(options_list[0], ' UNION ALL '.join(queries), params)
        for res in self._cr.dictfetchall():
            # Build the key.
            key = [res['period_index']]
            if not self.groupby:
                for gb in groupby_list:
                    key.append(res[gb])
            key = tuple(key)

            # Compute values.
            results['count_rows'].setdefault(res['period_index'], 0)
            results['count_rows'][res['period_index']] += res['count_rows']
            if key not in results['sum']:
                results['sum'][key] = 0
                results['sum_if_pos'][key] = 0
                results['sum_if_neg'][key] = 0
            results['sum'][key] += res['balance']
            if res['balance'] > 0:
                results['sum_if_pos'][key] += res['balance']
            if res['balance'] < 0:
                results['sum_if_neg'][key] += res['balance']

        return results
