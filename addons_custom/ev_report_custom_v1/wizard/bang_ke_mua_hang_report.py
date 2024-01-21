import pandas as pd

from odoo.addons.ev_report.wizards.report_base import _money_format
from odoo import fields, models, _


class BangKeMuaHangReport(models.TransientModel):
    _name = "bang.ke.mua.hang.report"
    _inherit = "report.base"
    _auto = True
    _description = "Bang Ke Mua Hang"

    to_date = fields.Date(string="To Date", required=True)
    amount = fields.Float(string="Total amount")

    def _get_default_template_view_external_id(self):
        return 'ev_report_custom_v1.bang_ke_mua_hang_data'

    def _get_report_json(self):
        params = self.copy_data()[0]
        data = self.env['bang.ke.mua.hang.store'].get_data(**params)
        compute_fields = self._compute_fields_total(data)
        self.amount = compute_fields['total_amount']
        return data

    def _compute_fields_total(self, data):
        df = pd.json_normalize(data)
        compute_fields = {}
        total_amount = 0
        if len(data) > 0:
            total_amount += df[['thanhtien']].sum(axis=0, skipna=True)['thanhtien']

        compute_fields.update({
            'total_amount': total_amount,
        })
        return compute_fields

    def _columns_name(self):
        return {
            '.no': _('STT'),
            'date_order': _('Invoice date'),
            'kho': _('Warehouse'),
            'nhomhh': _('Commodity group'),
            'msp': _('Product code'),
            'tensp': _('Product name'),
            'dvt': _('Unit'),
            'qty_buy': _('Qty buy'),
            'gia': _('Price'),
            'thanhtien': _('Total money'),
            'ma_ncc': _('Code partner'),
        }

    def _header_merge(self):
        return [['0:0', '0:0', '.no']]

    def _columns_width(self):
        return {
            '.no': '10px; text-align: center',
            'date_order': '65px; text-align: center',
            'kho': '80px; text-align: center',
            'nhomhh': '105px; text-align: center',
            'msp': '60px; text-align: center',
            'tensp': '300px; text-align: center',
            'dvt': '10px; text-align: center',
            'qty_buy': '20px; text-align: center',
            'gia': '10px; text-align: center',
            'thanhtien': '40px; text-align: center',
            'ma_ncc': '40px; text-align: center',
        }

    def _footer_merge(self):
        total_amount = _money_format(self.amount)
        return [
            ['8:0', '8:0', _('Total amount')],
            ['9:0', '9:0', total_amount]
        ]
