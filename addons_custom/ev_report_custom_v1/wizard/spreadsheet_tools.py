# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _, exceptions
from odoo.addons.ev_report.wizards.report_base import _money_format


class SpreadsheetTools(models.TransientModel):
    _name = "spreadsheet.tools"
    _inherit = 'report.base'
    _auto = True
    _description = _("Spreadsheet Tools")

    def _get_default_template_view_external_id(self):
        return 'ev_report_custom_v1.spreadsheet_tools_template'

    from_date = fields.Date(string='From date',
                            required=True,
                            default=lambda x: datetime.today().replace(day=1))
    to_date = fields.Date(string='To date',
                          required=True,
                          default=lambda x:
                          (datetime.today().replace(day=1)
                           + relativedelta(months=1)) - relativedelta(days=1))

    # field sum
    total_original = fields.Float(store=False)
    total_start_value = fields.Float(store=False)
    total_depreciated_value = fields.Float(store=False)
    total_residual_value = fields.Float(store=False)
    total_value_in_period = fields.Float(store=False)

    _sql_constraints = [
        ('date_check', "CHECK(from_date<=to_date)",
         "The start date must be earlier than the end date!")
    ]

    def get_download_file_name(self):
        return _('spreadsheet_tools.xlsx')

    def _get_report_json(self):
        params = self.copy_data()[0]
        Store = self.env['spreadsheet.tools.store']
        data = Store.get_data(**params)

        self.total_original = data['summary']['total_original']
        self.total_start_value = data['summary']['total_start_value']
        self.total_depreciated_value = data['summary']['total_depreciated_value']
        self.total_residual_value = data['summary']['total_residual_value']
        self.total_value_in_period = data['summary']['total_value_in_period']

        return data['data']

    def _columns_name(self):
        return {
            '.no': _('.No'),
            'tents': _('Asset Name'),
            'mats': _('Asset Code'),
            'ngaytinhkh': _('Depreciation Date'),
            'sokyhk': _('Method Number'),
            'trangthai': _('State'),
            'nguyengia': _('Original'),
            'gtbatdaukh': _('Start Allocation Value'),
            'gtdakh': _('Allocation Value'),
            'gtconlai': _('Residual Value'),
            'gtkhtrongky': _('Allocation Value in Period'),
        }

    def _columns_width(self):
        return {
            '.no': '60px',
            'mats': '150px',
            'ngaytinhkh': '150px',
            'sokyhk': '120px',
            'trangthai': '140px',
            'nguyengia': '160px',
            'gtbatdaukh': '160px',
            'gtdakh': '160px',
            'gtconlai': '160px',
            'gtkhtrongky': '160px',
        }

    def _header_merge(self):
        return [
            ['0:0', '0:0', '.no'],
        ]

    def _footer_merge(self):
        return [
            ['0:0', '5:0', _('SUM')],
            ['6:0', '6:0', _money_format(self.total_original)],
            ['7:0', '7:0', _money_format(self.total_start_value)],
            ['8:0', '8:0', _money_format(self.total_depreciated_value)],
            ['9:0', '9:0', _money_format(self.total_residual_value)],
            ['10:0', '10:0', _money_format(self.total_value_in_period)],
        ]
