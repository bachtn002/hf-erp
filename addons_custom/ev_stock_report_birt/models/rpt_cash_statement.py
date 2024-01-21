# -*- coding: utf-8 -*-
import odoo.tools.config as config

from odoo import models, fields, api, exceptions


class RPTCashStatement(models.TransientModel):
    _name = 'rpt.cash.statement'

    date = fields.Date('Date')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    def action_export_report(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date = self.date.strftime('%d/%m/%Y')
        report_name = "rpt_cash_statement.rptdesign"
        param_str = {
            '&company_id': self.company_id.id,
            '&date': date,
        }
        birt_link = birt_url + report_name
        return {
            "type": "ir.actions.client",
            'name': 'Inventory Report',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link,
                'payload_data': param_str,
            }
        }
