# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, exceptions
import numpy as np


class ToolsTrackingMonthReport(models.TransientModel):
    _name = "tools.tracking.month.report"
    _inherit = 'report.base'
    _auto = True
    _description = _("Tools Tracking Month Report")

    def _get_default_template_view_external_id(self):
        return 'ev_report_custom_v1.tools_tracking_month_report_template'

    from_date = fields.Date(string='From date', required=True)
    to_date = fields.Date(string='To date', required=True)

    report_type = fields.Selection(default='pivot')

    _sql_constraints = [
        ('date_check', "CHECK(from_date<=to_date)",
         "The start date must be earlier than the end date!")
    ]

    def get_download_file_name(self):
        return _('tools_tracking_month_report.xlsx')

    def _get_report_json(self):
        params = self.copy_data()[0]
        Store = self.env['tools.tracking.month.report.store']

        return Store.get_data(**params)

    def _build_report_pandas_pivot(self, data):
        pv = super(ToolsTrackingMonthReport,
                   self)._build_report_pandas_pivot(data)
        pv = pv[[pv.columns[-1], *pv.columns[:-1]]]
        pv = pv.rename(columns={pv.columns[0]: _('Total Depreciation')})
        return pv

    def prepare_report_pivot_configs(self):
        values = ['gtkhauhao']
        index = ['mataisan', 'tentaisan', 'giatriconlai']
        columns = ['thangkhauhao']
        return {
            'values': values,
            'index': index,
            'columns': columns,
            'aggfunc': np.sum,
            'margins': True,
            'margins_name': _('Total'),
        }

    def _cook_soup(self, soup):
        tbody = soup.find('tbody')
        for tr in tbody.findAll('tr'):
            tr['style'] = [
                'font-size: 14px; font-family: Times New Roman']
            ths = tr.findAll('th')
            if len(ths) > 2:
                ths[2]['style'] = ['text-align: right !important']
                if ths[2].string != None:
                    ths[2].string = f'{float(ths[2].text):,.2f}'.replace(
                        '.', '|').replace(',', '.').replace('|', ',')

    def _columns_width(self):
        return {
            'mataisan': '180px',
            'giatriconlai': '180px',
        }

    def _columns_name(self):
        return {
            'mataisan': _('Asset Code'),
            'tentaisan': _('Asset Name'),
            'giatriconlai': _('Residual Value'),
            'thangkhauhao': '',
        }
