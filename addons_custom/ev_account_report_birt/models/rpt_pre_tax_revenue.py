import odoo.tools.config as config

from odoo import api, models, fields
from odoo.exceptions import ValidationError


class RPTPreTaxRevenue(models.TransientModel):
    _name = 'rpt.pre.tax.revenue'

    from_date = fields.Date('From date')
    to_date = fields.Date('To date')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    def _get_param(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date_from = self.from_date.strftime('%d/%m/%Y')
        to_date = self.to_date.strftime('%d/%m/%Y')
        param_str = {
            '&company_id': self.company_id.id,
            '&pos_shop': '0',
            '&from_date': date_from,
            '&to_date': to_date,
        }
        report_name = "rpt_pre_tax_revenue.rptdesign"
        birt_link = birt_url + report_name
        return birt_link, param_str

    def action_export_report(self):
        birt_link, param_str = self._get_param()
        return {
            "type": "ir.actions.client",
            'name': 'Pre tax revenue Report',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link,
                'payload_data': param_str,
            }
        }

    def action_report_excel(self):
        birt_link, param_str = self._get_param()
        return {
            "type": "ir.actions.client",
            'name': 'Pre tax revenue Report',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link + '&__format=xlsx',
                'payload_data': param_str,
            }
        }
