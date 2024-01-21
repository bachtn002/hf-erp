import odoo.tools.config as config

from odoo import api, models, fields
from odoo.exceptions import ValidationError


class RPTBalancesArising(models.TransientModel):
    _name = 'rpt.balances.arising'

    from_date = fields.Date('From date')
    to_date = fields.Date('To date')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    def _get_param(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date_from = self.from_date.strftime('%d/%m/%Y')
        date_to = self.to_date.strftime('%d/%m/%Y')
        param_str = {
            '&company_id': self.company_id.id,
            '&date_from': date_from,
            '&date_to': date_to,
        }
        report_name = "report_balances_arising.rptdesign"
        birt_link = birt_url + report_name
        return birt_link, param_str

    def action_export_report(self):
        birt_link, param_str = self._get_param()
        return {
            "type": "ir.actions.client",
            'name': 'Balances Arising',
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
            'name': 'Balances Arising',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link + '&__format=xlsx',
                'payload_data': param_str,
            }
        }
