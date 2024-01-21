# -*- coding: utf-8 -*-
import odoo.tools.config as config
from odoo import models, fields, api, exceptions


class RPTStockDocument(models.TransientModel):
    _name = 'rpt.stock.document'

    name = fields.Char(string='Inventory Report')
    location_ids = fields.Many2many('stock.location', string='Locations')
    product_ids = fields.Many2many('product.product', string='Products')
    from_date = fields.Date('From date')
    to_date = fields.Date('To date')
    state = fields.Selection([
        ('no_done', 'No Done'),
        ('done', 'Done')],
        default='no_done',string="State")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    x_all_internal = fields.Boolean('All Internal')

    @api.onchange('x_all_internal')
    def _onchange_all_internal(self):
        if self.x_all_internal:
            loaction_ids = self.env['stock.location'].search([('usage', '=', 'internal'), ('company_id', '=', self.company_id.id)])
            self.location_ids = [(6, 0, loaction_ids.ids)]
        else:
            self.location_ids = [(5, 0, 0)]

    def action_export_report(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date_from = self.from_date.strftime('%d/%m/%Y')
        date_to = self.to_date.strftime('%d/%m/%Y')
        location_ids = ','.join([str(idd) for idd in self.location_ids.ids]) if self.location_ids else '0'
        product_ids = ','.join([str(idd) for idd in self.product_ids.ids]) if self.product_ids else '0'
        report_name = ''
        if self.state == 'no_done':
            report_name = "rpt_stock_document_user_no_done.rptdesign"
        else:
            report_name = "rpt_stock_document_user_done.rptdesign"
        param_str = {
            '&from_date': date_from,
            '&to_date': date_to,
            '&location_ids': location_ids,
            '&product_ids': product_ids,
            '&company_id': self.company_id.id,
        }
        birt_link = birt_url + report_name
        return {
            "type": "ir.actions.client",
            'name': 'Inventory Document Report',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link,
                'payload_data': param_str,
            }
        }
    def action_export_report_accountent(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date_from = self.from_date.strftime('%d/%m/%Y')
        date_to = self.to_date.strftime('%d/%m/%Y')
        location_ids = ','.join([str(idd) for idd in self.location_ids.ids]) if self.location_ids else '0'
        product_ids = ','.join([str(idd) for idd in self.product_ids.ids]) if self.product_ids else '0'
        report_name = ''
        if self.state == 'no_done':
            report_name = "rpt_stock_document_accountent_no_done.rptdesign"
        else:
            report_name = "rpt_stock_document_accountant_done.rptdesign"
        param_str = {
            '&from_date': date_from,
            '&to_date': date_to,
            '&location_ids': location_ids,
            '&product_ids': product_ids,
            '&company_id': self.company_id.id,
        }
        birt_link = birt_url + report_name
        return {
            "type": "ir.actions.client",
            'name': 'Inventory Document Report',
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
        date_from = self.from_date.strftime('%d/%m/%Y')
        date_to = self.to_date.strftime('%d/%m/%Y')
        location_ids = ','.join([str(idd) for idd in self.location_ids.ids]) if self.location_ids else '0'
        product_ids = ','.join([str(idd) for idd in self.product_ids.ids]) if self.product_ids else '0'
        report_name = "rpt_stock_document.rptdesign"
        param_str = {
            '&from_date': date_from,
            '&to_date': date_to,
            '&location_ids': location_ids,
            '&product_ids': product_ids,
            '&company_id': self.company_id.id,
        }
        birt_link = birt_url + report_name
        return {
            "type": "ir.actions.client",
            'name': 'Inventory Document Report',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link + '&__format=xlsx',
                'payload_data': param_str,
            }
        }
