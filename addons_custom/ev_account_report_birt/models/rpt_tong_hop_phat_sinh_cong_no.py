# -*- coding: utf-8 -*-
import odoo.tools.config as config
from odoo import models, fields, api, exceptions
from datetime import datetime


class RptTongHopPhatSinhCongNo(models.TransientModel):
    _name = 'report.tong.hop.phat.sinh.cong.no'

    date_from = fields.Date('From date')
    date_to = fields.Date('To date')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    account_id = fields.Many2one('account.account', string='Account')
    partner_ids = fields.Many2many('res.partner', string='Vendors')

    def _get_param(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date_from = self.date_from.strftime('%d/%m/%Y')
        to_date = self.date_to.strftime('%d/%m/%Y')
        param_str = {
            '&from_date': date_from,
            '&to_date': to_date,
            '&partner_id': ','.join([str(idd) for idd in self.partner_ids.ids]) if self.partner_ids else '0',
            '&account_id': self.account_id.id,
            '&company_id': self.company_id.id
        }
        report_name = "Bang_tong_hop_phat_sinh_cong_no_theo_NCC.rptdesign"
        birt_link = birt_url + report_name
        return birt_link, param_str

    def action_export_report(self):
        birt_link, param_str = self._get_param()
        return {
            "type": "ir.actions.client",
            'name': 'Synthesize incurred debt Report',
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
            'name': 'Synthesize incurred debt Report',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link + '&__format=xlsx',
                'payload_data': param_str,
            }
        }
