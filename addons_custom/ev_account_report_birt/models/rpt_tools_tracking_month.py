import odoo.tools.config as config

from odoo import api, models, fields
from odoo.exceptions import ValidationError


class RPTToolsTrackingMonth(models.TransientModel):
    _name = 'rpt.tools.tracking.month'

    from_date = fields.Date('From date')
    to_date = fields.Date('To date')

    def _get_param(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date_from = self.from_date.strftime('%d/%m/%Y')
        to_date = self.to_date.strftime('%d/%m/%Y')
        param_str = {
            '&from_date': date_from,
            '&to_date': to_date,
        }
        report_name = "rpt_tools_tracking_month.rptdesign"
        birt_link = birt_url + report_name
        return birt_link, param_str

    def action_export_report(self):
        birt_link, param_str = self._get_param()
        return {
            "type": "ir.actions.client",
            'name': 'Tools Tracking Month',
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
            'name': 'Tools Tracking Month',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link + '&__format=xlsx',
                'payload_data': param_str,
            }
        }
