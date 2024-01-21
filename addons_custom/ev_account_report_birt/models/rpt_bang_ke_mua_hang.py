import odoo.tools.config as config
from odoo import models, fields, api, exceptions
from datetime import datetime


class RptBangKeMuaHang(models.TransientModel):
    _name = 'report.bang.ke.mua.hang'
    date = fields.Date('Date')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    def _get_param(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date = self.date.strftime('%d/%m/%Y')
        param_str = {
            '&date': date,
            '&company_id': self.company_id.id
        }
        report_name = "bangkemuahang.rptdesign"
        birt_link = birt_url + report_name
        return birt_link, param_str

    def action_export_report(self):
        birt_link, param_str = self._get_param()
        return {
            "type": "ir.actions.client",
            'name': 'List Purchase Report',
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
            'name': 'list Purchase Report',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link + '&__format=xlsx',
                'payload_data': param_str,
            }
        }
