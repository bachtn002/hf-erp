# -*- coding: utf-8 -*-
import odoo.tools.config as config
from odoo import models, fields, api, exceptions
from datetime import datetime


class RPTALLInOutWarehosue(models.TransientModel):
    _name = 'rpt.all.in.out.warehouse'

    date_from = fields.Date('From date')
    date_to = fields.Date('To date')
    type = fields.Selection([
        ('in', 'License IN'),
        ('out', 'License Out')],
        string='Type License', default='in')

    def _get_param(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date_from = self.date_from.strftime('%d/%m/%Y')
        date_to = self.date_to.strftime('%d/%m/%Y')
        param_str = {
            '&from_date': date_from,
            '&to_date': date_to,
        }
        report_name = ''
        if self.type == 'in':
            report_name = "tong_hop_nhap_theo_giao_dich_kho.rptdesign"
        else:
            report_name = "tong_hop_xuat_theo_giao_dich_kho.rptdesign"
        birt_link = birt_url + report_name
        return birt_link, param_str

    def action_export_report(self):
        birt_link, param_str = self._get_param()
        return {
            "type": "ir.actions.client",
            'name': 'License In Out Warehouse Report',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link,
                'payload_data': param_str,
            }
        }
