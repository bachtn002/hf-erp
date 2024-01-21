import odoo.tools.config as config

from odoo import api, models, fields
from odoo.exceptions import ValidationError


class RPTDetailedLedger(models.TransientModel):
    _name = 'rpt.detailed.ledger'

    from_date = fields.Date('From date')
    to_date = fields.Date('To date')
    account_id = fields.Many2one('account.account', 'Account')
    is_like = fields.Boolean('Is Like Account', default=False)
    account_is_like = fields.Char('Account')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    def _get_param(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date_from = self.from_date.strftime('%d/%m/%Y')
        to_date = self.to_date.strftime('%d/%m/%Y')
        param_str = {
        }
        report_name = ''
        if not self.is_like:
            report_name = "So_chi_tiet_tai_khoan.rptdesign"
            param_str = {
                '&company_id': self.company_id.id,
                '&account_id': self.account_id.code,
                '&from_date': date_from,
                '&to_date': to_date,
            }
        else:
            report_name = "So_chi_tiet_tai_khoan_like.rptdesign"
            param_str = {
                '&company_id': self.company_id.id,
                '&account_id': self.account_is_like,
                '&from_date': date_from,
                '&to_date': to_date,
            }
        birt_link = birt_url + report_name
        return birt_link, param_str

    def action_export_report(self):
        birt_link, param_str = self._get_param()
        return {
            "type": "ir.actions.client",
            'name': 'Detailed Ledger',
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
            'name': 'Detailed Ledger',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link + '&__format=xlsx',
                'payload_data': param_str,
            }
        }
