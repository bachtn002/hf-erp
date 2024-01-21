# -*- coding: utf-8 -*-
import odoo.tools.config as config
from odoo import models, fields, api, exceptions
from datetime import datetime


class RptDetailDebitNCC(models.TransientModel):
    _name = 'report.detail.debit.ncc'

    date_from = fields.Date('From date')
    date_to = fields.Date('From date')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    partner_id = fields.Many2many('res.partner', string='Partner')
    account_id = fields.Many2one('account.account', 'Account')

    def _get_param(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date_from = self.date_from.strftime('%d/%m/%Y')
        date_to = self.date_to.strftime('%d/%m/%Y')
        param_str = {
            '&date_from': date_from,
            '&date_to': date_to,
            '&partner_id': ','.join(str(x.id) for x in self.partner_id) or '0',
            '&company_id': self.company_id.id,
            '&contra_account_id': self.account_id.id
        }
        report_name = "CT_cong_no_NCC.rptdesign"
        birt_link = birt_url + report_name
        return birt_link, param_str

    def action_export_report(self):
        birt_link, param_str = self._get_param()
        return {
            "type": "ir.actions.client",
            'name': 'Detail Debit Report',
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
            'name': 'Detail Debit Report',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link + '&__format=xlsx',
                'payload_data': param_str,
            }
        }
