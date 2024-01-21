# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, exceptions
from odoo.addons.ev_report.wizards.report_base import _money_format

class PreTaxRevenueReport(models.TransientModel):
    _name = "pre.tax.revenue.report"
    _inherit = 'report.base'
    _auto = True
    _description = _("Pre Tax Revenue Report")

    def _get_default_template_view_external_id(self):
        return 'ev_report_custom_v1.pre_tax_revenue_report_template'

    from_date = fields.Date(string='From date', required=True)
    to_date = fields.Date(string='To date', required=True)

    #field sum
    total_revenue = fields.Float(store = False)
    total_revenue_refund = fields.Float(store =False)
    total_cost = fields.Float(store=False)
    total_profit = fields.Float(store = False)

    @api.onchange('from_date','to_date')
    def _onchange_from_to_date(self):
        if self.from_date and self.to_date:
            if self.from_date > self.to_date:
                raise exceptions.UserError(
                        _("The start date must be earlier than the end date!"))

    def get_download_file_name(self):
        return _('pre_tax_revenue_report.xlsx')

    def _get_report_json(self):
        params = self.copy_data()[0]
        Store = self.env['pre.tax.revenue.report.store']
        data = Store.get_data(**params)

        self.total_revenue = data['summary']['total_revenue']
        self.total_revenue_refund = data['summary']['total_revenue_refund']
        self.total_cost = data['summary']['total_cost']
        self.total_profit = data['summary']['total_profit']

        return data['data']

    def _columns_name(self):
        return {
            '.no': _('.No'),
            'shop_name': _('Shop Name'),
            'revenue': _('Revenue'),
            'revenue_refund': _('Revenue Refund'),
            'giavon': _('Cost'),
            'loinhuan': _('Profit'),
        }

    def _columns_width(self):
        return {
            '.no': '60px',
            'revenue': '200px',
            'revenue_refund': '200px',
            'giavon': '200px',
            'loinhuan': '200px',
        }

    def _header_merge(self):
        return [
            ['0:0', '0:0', '.no'],
        ]

    def _footer_merge(self):
        return [
            ['0:0', '0:0'],
            ['1:0', '1:0', _('SUM')],
            ['2:0', '2:0', _money_format(self.total_revenue)],
            ['3:0', '3:0', _money_format(self.total_revenue_refund)],
            ['4:0', '4:0', _money_format(self.total_cost)],
            ['5:0', '5:0', _money_format(self.total_profit)],
        ]

