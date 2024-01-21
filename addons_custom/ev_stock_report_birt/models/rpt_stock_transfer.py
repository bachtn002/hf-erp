# -*- coding: utf-8 -*-
import odoo.tools.config as config

from odoo import models, fields, api, exceptions


class RPTStockTransfer(models.TransientModel):
    _name = 'rpt.stock.transfer'

    name = fields.Char(string='Inventory Report Stock transfer')
    from_date = fields.Date('From date')
    to_date = fields.Date('To date')
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouse')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.user', string='user', default=lambda self: self.env.user)

    def action_export_report(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date_to = self.to_date.strftime('%d/%m/%Y')
        date_from = self.from_date.strftime('%d/%m/%Y')
        warehouse_ids = ','.join([str(idd) for idd in self.warehouse_ids.ids]) if self.warehouse_ids else '0'
        report_name = "rpt_stock_transfer.rptdesign"
        param_str = {
            '&company_id': self.company_id.id,
            '&from_date': date_from,
            '&to_date': date_to,
            '&warehouse_ids': warehouse_ids,
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

    def action_report_excel(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date_to = self.to_date.strftime('%d/%m/%Y')
        date_from = self.from_date.strftime('%d/%m/%Y')
        warehouse_id = ','.join([str(idd) for idd in self.warehouse_ids.ids]) if self.warehouse_ids else '0'
        report_name = "rpt_stock_transfer.rptdesign"
        param_str = {
            '&company_id': self.company_id.id,
            '&from_date': date_from,
            '&to_date': date_to,
            '&warehouse_id': warehouse_id,
        }
        birt_link = birt_url + report_name
        return {
            "type": "ir.actions.client",
            'name': 'Inventory Report',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link + '&__format=xlsx',
                'payload_data': param_str,
            }
        }

    @api.onchange('user_id')
    def _onchange_domain_warehouse(self):
        if self.user_id:
            if self.user_id.warehouse_ids:
                return {'domain': {'warehouse_ids': [('id', 'in', self.region_ids.ids)]}}
            else:
                return {'domain': {'warehouse_ids': [(1, '=', 1)]}}
