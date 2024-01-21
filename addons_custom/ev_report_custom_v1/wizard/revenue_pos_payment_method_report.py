# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from odoo.exceptions import UserError

from odoo import api, fields, models, _, exceptions


class RevenuePosPaymentMethodReport(models.TransientModel):
    _name = "revenue.pos.payment.method.report"
    _inherit = 'report.base'
    _auto = True
    _description = _("Revenue Pos Payment Method Report")

    def _get_default_template_view_external_id(self):
        return 'ev_report_custom_v1.revenue_pos_payment_method_template'

    from_date = fields.Date(string='From date', required=True)
    to_date = fields.Date(string='To date', required=True)

    report_type = fields.Selection(default='pivot')

    _sql_constraints = [
        ('date_check', "CHECK(from_date<=to_date)",
         "The start date must be earlier than the end date!")
    ]

    def get_download_file_name(self):
        return _('revenue_pos_payment_method_report.xlsx')

    def _get_report_json(self):
        date_from = self.from_date.strftime('%d/%m/%Y')
        date_to = self.to_date.strftime('%d/%m/%Y')
        pos_shop_ids = self.env.user.x_pos_shop_ids
        if self.env.user.x_view_all_shop:
            pos_shop_ids = '0'
        else:
            if pos_shop_ids:
                pos_shop_ids = ','.join([str(idd) for idd in pos_shop_ids.ids])
            else:
                raise UserError(_('User not posh shop'))

        Store = self.env['revenue.pos.payment.method.report.store']

        return Store.get_data(**{'date_from': date_from, 'date_to': date_to,
                                 'pos_shop_ids': pos_shop_ids})

    def _build_report_pandas_pivot(self, data):
        df = pd.json_normalize(data)
        pivot_configs = self.prepare_report_pivot_configs()
        configs = pivot_configs
        pv = pd.pivot_table(df, **configs)
        pv = pv.droplevel(0, 1)
        pv = pv.fillna(0)
        g = pv.groupby(level=0).sum()
        m = pd.concat([g], keys=[_('TOTAL')], names=['to_date']).swaplevel(0, 1)
        m = pd.concat([m], keys=[''], names=['name_shop']).swaplevel(0, 1)
        m = pd.concat([m], keys=[''], names=['code_shop']).swaplevel(0, 1)
        pv = pd.concat([pv, m], axis=0).sort_index(level=0)
        pv = pv.head(-1)
        return pv

    def prepare_report_pivot_configs(self):
        values = ['sum']
        index = ['date_group', 'code_shop', 'name_shop', 'to_date']
        columns = ['payment_method']
        return {
            'values': values,
            'index': index,
            'columns': columns,
            'aggfunc': np.sum,
            'margins': True,
            'margins_name': _('Total'),
        }

    def _header_merge(self):
        return [
            ['0:0', '0:1', 'date_group'],
            ['1:0', '1:1', 'code_shop'],
            ['2:0', '2:1', 'name_shop'],
            ['3:0', '3:1', 'to_date'],
        ]

    def _columns_name(self):
        return {
            'date_group': _('Date Group'),
            'code_shop': _('Code Shop'),
            'name_shop': _('Name Shop'),
            'to_date': _('Date'),
        }

    def action_report(self):
        return super(RevenuePosPaymentMethodReport, self.with_context(renew=True)).action_report()
