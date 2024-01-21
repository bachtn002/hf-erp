# -*- coding: utf-8 -*-
import odoo.tools.config as config
from odoo import models, fields, api, exceptions
from odoo.exceptions import UserError


class RptPosReport(models.TransientModel):
    _name = 'rpt.pos.report'

    name = fields.Char(string='Pos Report')
    from_date = fields.Date('From date')
    to_date = fields.Date('To date')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    def action_export_report_pos_order_line(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date_from = self.from_date.strftime('%d/%m/%Y')
        date_to = self.to_date.strftime('%d/%m/%Y')
        pos_shop_ids = self.env.user.x_pos_shop_ids
        if self.env.user.x_view_all_shop:
            pos_shop_ids = '0'
        else:
            if pos_shop_ids:
                pos_shop_ids = ','.join([str(idd) for idd in pos_shop_ids.ids])
            else:
                raise UserError(_('User not posh shop'))
        report_name = "rpt_pos_order_line.rptdesign"
        param_str = {
            '&from_date': date_from,
            '&to_date': date_to,
            '&company_id': self.company_id.id,
            '&pos_shop': pos_shop_ids,
        }
        birt_link = birt_url + report_name
        return {
            "type": "ir.actions.client",
            'name': 'Pos Order Line Report',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link,
                'payload_data': param_str,
            }
        }

    def action_report_excel_pos_order_line(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date_from = self.from_date.strftime('%d/%m/%Y')
        date_to = self.to_date.strftime('%d/%m/%Y')
        report_name = "rpt_pos_order_line.rptdesign"
        pos_shop_ids = self.env.user.x_pos_shop_ids
        if self.env.user.x_view_all_shop:
            pos_shop_ids = '0'
        else:
            if pos_shop_ids:
                pos_shop_ids = ','.join([str(idd) for idd in pos_shop_ids.ids])
            else:
                raise UserError(_('User not posh shop'))
        param_str = {
            '&from_date': date_from,
            '&to_date': date_to,
            '&company_id': self.company_id.id,
            '&pos_shop': pos_shop_ids,
        }
        birt_link = birt_url + report_name
        return {
            "type": "ir.actions.client",
            'name': 'Pos Order Line Report',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link + '&__format=xlsx',
                'payload_data': param_str,
            }
        }

    def action_export_report_revenue_pos_payment_method(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date_from = self.from_date.strftime('%d/%m/%Y')
        date_to = self.to_date.strftime('%d/%m/%Y')
        report_name = "rpt_revenue_pos_payment_method.rptdesign"
        pos_shop_ids = self.env.user.x_pos_shop_ids
        if self.env.user.x_view_all_shop:
            pos_shop_ids = '0'
        else:
            if pos_shop_ids:
                pos_shop_ids = ','.join([str(idd) for idd in pos_shop_ids.ids])
            else:
                raise UserError(_('User not posh shop'))
        param_str = {
            '&from_date': date_from,
            '&to_date': date_to,
            '&company_id': self.company_id.id,
            '&pos_shop': pos_shop_ids,
        }
        birt_link = birt_url + report_name
        return {
            "type": "ir.actions.client",
            'name': 'Revenue Pos Payment Method Report',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link,
                'payload_data': param_str,
            }
        }

    def action_report_excel_revenue_pos_payment_method(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date_from = self.from_date.strftime('%d/%m/%Y')
        date_to = self.to_date.strftime('%d/%m/%Y')
        report_name = "rpt_revenue_pos_payment_method.rptdesign"
        pos_shop_ids = self.env.user.x_pos_shop_ids
        if self.env.user.x_view_all_shop:
            pos_shop_ids = '0'
        else:
            if pos_shop_ids:
                pos_shop_ids = ','.join([str(idd) for idd in pos_shop_ids.ids])
            else:
                raise UserError(_('User not posh shop'))
        param_str = {
            '&from_date': date_from,
            '&to_date': date_to,
            '&company_id': self.company_id.id,
            '&pos_shop': pos_shop_ids,
        }
        birt_link = birt_url + report_name
        return {
            "type": "ir.actions.client",
            'name': 'Revenue Pos Payment Method Report',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link + '&__format=xlsx',
                'payload_data': param_str,
            }
        }


