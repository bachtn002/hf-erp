# -*- coding: utf-8 -*-
from time import sleep

import requests
import json
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

from ..helpers import APIZNS
from datetime import datetime, timedelta, date

_logger = logging.getLogger(__name__)


class ZNSInformation(models.Model):
    _name = 'zns.information'
    _description = 'Zalo Notification Service Information'
    _rec_name = 'tracking_id'
    _order = 'create_date desc'

    order_id = fields.Many2one('pos.order', 'Order', required=True)
    msg_id = fields.Char('MSG ID')
    tracking_id = fields.Char('Tracking ID', default=lambda self: _('New'), required=True, readonly=True)
    template_id = fields.Many2one('zns.template', 'Template')
    type = fields.Selection([
        ('order', 'Order')
    ], string='Type', default=None)

    order_code = fields.Char('Order Code')
    order_date = fields.Datetime('Order Date')
    phone = fields.Char('Phone')
    customer_name = fields.Char('Customer Name')
    order_value = fields.Integer('Order Value')
    point_plus = fields.Integer('Point Plus')
    point_value = fields.Integer('Point Value')
    shop_name = fields.Char('Shop Name')
    shop_id = fields.Many2one('pos.shop', 'Shop Name')

    sent_time = fields.Datetime('Sent Time')
    mess_error = fields.Char('Message Error')
    data = fields.Text('Data')

    type_send_id = fields.Many2one('type.send.zns', 'Type Send Zns')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('queue', 'Queue'),
        ('error', 'Error'),
        ('quota', 'Quota'),
        ('done', 'Done')],
        'State', default='draft')

    def action_send_zns(self):
        try:
            if not self.phone:
                return

            if self.state == 'draft':
                self.state = 'queue'
                # self._action_done()
                self.sudo().with_delay(channel='root.action_send_zns', max_retries=3)._action_done()
        except Exception as e:
            raise ValidationError(e)

    def _action_done(self):
        retry_times = 2
        while (retry_times > 0):
            try:
                base_url = self.env['ir.config_parameter'].sudo().get_param('url_api_zalo')
                url = base_url + '/zalo_oa/send_message'

                data = {}
                if self.type == 'order':
                    data = self.data_order_zns()
                    data['data']['tracking_id'] = self.tracking_id
                    data['oa_id'] = self.template_id.oa_id
                    data['app_id'] = self.template_id.app_id
                self.data = data
                response = requests.post(url, data=json.dumps(data),
                                         headers={'Content-Type': 'application/json'},
                                         verify=False)
                response = response.json()
                retry_times -= 2
                if response.get('error'):
                    if response.get('error').get('code') == '400':
                        self.mess_error = response.get('error').get('message')
                        self.state = 'error'
                    elif response.get('error').get('code') == '-211':
                        self.mess_error = response.get('error').get('message')
                        self.state = 'quota'
                elif response.get('result'):
                    if response.get('result').get('code') == '400':
                        self.mess_error = response.get('result').get('message')
                        self.state = 'error'
                    elif response.get('result').get('code') == '-211':
                        self.mess_error = response.get('result').get('message')
                        self.state = 'quota'
                    elif response.get('result').get('code') == 200:
                        self.msg_id = response.get('result').get('data').get('data').get('msg_id')
                        sent_time = datetime.fromtimestamp(
                            float(response.get('result').get('data').get('data').get('sent_time')) / 1000).strftime(
                            '%Y-%m-%d %H:%M:%S')
                        date_convert = datetime.strptime(sent_time, '%Y-%m-%d %H:%M:%S')
                        self.sent_time = date_convert
                        self.state = 'done'
            except requests.exceptions.ConnectionError as e:
                retry_times -= 1
                # if we run out of times retry then raise error instead
                if retry_times == 0:
                    raise ValidationError(e)
                sleep(1)
                continue
            except Exception as e:
                raise ValidationError(e)

    def data_order_zns(self):
        try:

            order_date = datetime.strftime(self.order_date + timedelta(hours=7), '%H:%m %d/%m/%Y')

            phone = '84' + self.phone.lstrip('0')

            data = {
                'type_send_zns': self.type_send_id.code,
                'authentication': self.type_send_id.token,
                'data': {
                    'phone': phone,
                    'template_id': self.template_id.template_id,
                    'template_data': {
                        'customer_name': self.customer_name,
                        'order_code': self.order_code,
                        'order_date': order_date,
                        'order_value': int(self.order_value),
                        'point_plus': int(self.point_plus),
                        'point_value': int(self.point_value),
                    }
                }

            }
            return data
        except Exception as e:
            raise ValidationError(e)

    def back_to_draft(self):
        try:
            if self.state == 'error':
                self.state = 'draft'
                self.sent_time = None
                self.mess_error = None
                self.data = None
        except Exception as e:
            raise ValidationError(e)

    @api.model
    def create(self, vals):
        try:
            seq = self.env['ir.sequence'].next_by_code('tracking.send.zns')
            vals['tracking_id'] = 'HOMEFARM/' + datetime.today().strftime('%d%m%Y') + '/' + seq
            return super(ZNSInformation, self).create(vals)
        except Exception as e:
            raise ValidationError(e)
