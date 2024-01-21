# -*- coding: utf-8 -*-
import odoo.tools.config as config
from odoo import models, fields, api, exceptions
from datetime import datetime


class RptDetailDebitByAccount(models.TransientModel):
    _name = 'rpt.detail.debit.by.account'

    date_from = fields.Date('From date')
    date_to = fields.Date('To date')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
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
            '&company_id': self.company_id.id,
            '&contra_account_id': self.account_id.id,
        }
        report_name = "bao_cao_chi_tiet_cong_no.rptdesign"
        birt_link = birt_url + report_name
        return birt_link, param_str

    def action_export_report(self):
        birt_link, param_str = self._get_param()
        return {
            "type": "ir.actions.client",
            'name': 'Detail Debit Account Report',
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
            'name': 'Detail Debit Account Report',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link + '&__format=xlsx',
                'payload_data': param_str,
            }
        }
