# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, exceptions
from odoo.addons.ev_report.wizards.report_base import _money_format


class ToolsTrackingReport(models.TransientModel):
    _name = "tools.tracking.report"
    _inherit = 'report.base'
    _auto = True
    _description = _("Tools Tracking Report")

    def _get_default_template_view_external_id(self):
        return 'ev_report_custom_v1.tools_tracking_report_template'

    from_date = fields.Date(string='From date', required=True)
    to_date = fields.Date(string='To date', required=True)

    # field sum
    total_original = fields.Float(store=False)
    total_start_value = fields.Float(store=False)
    total_depreciated_value = fields.Float(store=False)
    total_value_in_period = fields.Float(store=False)
    total_residual_value = fields.Float(store=False)
    total_average_depreciation = fields.Float(store=False)

    _sql_constraints = [
        ('date_check', "CHECK(from_date<=to_date)",
         "The start date must be earlier than the end date!")
    ]

    def get_download_file_name(self):
        return _('tools_tracking_report.xlsx')

    def _get_report_json(self):
        params = self.copy_data()[0]
        Store = self.env['tools.tracking.report.store']
        data = Store.get_data(**params)

        self.total_original = data['summary']['total_original']
        self.total_start_value = data['summary']['total_start_value']
        self.total_depreciated_value = data['summary']['total_depreciated_value']
        self.total_value_in_period = data['summary']['total_value_in_period']
        self.total_residual_value = data['summary']['total_residual_value']
        self.total_average_depreciation = data['summary']['total_average_depreciation']

        return data['data']

    def _columns_name(self):
        return {
            '.no': _('.No'),
            'mats': _('Tools code'),
            'tents': _('Tools Name'),
            'trangthai': _('State'),
            'nguyengia': _('Original'),
            'gtbatdaukh': _('Start Allocation Value'),
            'gtdakh': _('Allocation Value'),
            'gtkhtrongky': _('Allocation Value in Period'),
            'gtconlai': _('Residual Value'),
            'gttbtrongky': _('Average Allocation'),
            'ngaymua': _('Date Arising'),
            'ngaytinhkh': _('Allocation Date'),
            'ngaygiam': _('End Date'),
            'sokyhk': _('Period Number'),
            'ngayct': _('Document Date'),
            'soct': _('Document Number'),
            'tktaisan': _('Tools Account'),
            'tkkhauhao': _('Allociation Account'),
            'tkchiphi': _('Fee Account'),
            'mabp': _('Apartment Code'),
            'maphi': _('Fee Code'),
            'tenphi': _('Fee Name'),
            'tenbp': _('Apartment Name'),
        }

    def _columns_width(self):
        return {
            '.no': '50px',
            'mats': '120px',
            'tents': '120px',
            'trangthai': '100px',
            'nguyengia': '120px',
            'gtbatdaukh': '120px',
            'gtdakh': '120px',
            'gtkhtrongky': '120px',
            'gtconlai': '120px',
            'gttbtrongky': '120px',
            'ngaymua': '90px',
            'ngaytinhkh': '90px',
            'ngaygiam': '90px',
            'sokyhk': '90px',
            'ngayct': '90px',
            'soct': '90px',
            'tktaisan': '90px',
            'tkkhauhao': '90px',
            'tkchiphi': '90px',
            'mabp': '90px',
            'maphi': '90px',
            'tenphi': '120px',
            'tenbp': '120px',
        }

    def _header_merge(self):
        return [
            ['0:0', '0:0', '.no'],
        ]

    def _footer_merge(self):
        return [
            ['0:0', '3:0', _('SUM')],
            ['4:0', '4:0', _money_format(self.total_original)],
            ['5:0', '5:0', _money_format(self.total_start_value)],
            ['6:0', '6:0', _money_format(self.total_depreciated_value)],
            ['7:0', '7:0', _money_format(self.total_value_in_period)],
            ['8:0', '8:0', _money_format(self.total_residual_value)],
            ['9:0', '0:0', _money_format(self.total_average_depreciation)],
            ['10:0', '22:0', ]
        ]
