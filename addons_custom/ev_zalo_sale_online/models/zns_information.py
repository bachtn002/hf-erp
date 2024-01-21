# -*- coding: utf-8 -*-
from time import sleep
import requests
import json
from odoo import fields, models
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class ZnsInformation(models.Model):
    _inherit = 'zns.information'

    order_id = fields.Many2one('pos.order', 'Order', required=False)
    minute = fields.Integer(string='Minute')
    type = fields.Selection(selection_add=[
        ('sale_online', 'Sale Online'),
        ('waiting_delivery', 'Waiting Delivery'),
        ('delivery', 'Delivery')
    ], string='Type', default=None)

    def action_send_zns_sale_online(self):
        try:
            if self.state == 'draft':
                self.state = 'queue'
                self.sudo().with_delay(channel='root.action_send_zns', max_retries=3)._action_done_sale_online()
        except Exception as e:
            raise ValidationError(e)

    def _action_done_sale_online(self):
        retry_times = 2
        while retry_times > 0:
            try:
                url = self.env['ir.config_parameter'].sudo().get_param('url_send_template')
                data = {}
                phone = '84' + self.phone.lstrip('0')

                template_data = self.get_param_template_custom()
                if self.type == 'sale_online':
                    data = {
                        'phone': phone,
                        'template_id': self.template_id.template_id,
                        'template_data': template_data,
                        'tracking_id': self.tracking_id
                    }
                elif self.type == 'waiting_delivery':
                    data = {
                        'phone': phone,
                        'template_id': self.template_id.template_id,
                        'template_data': template_data,
                        'tracking_id': self.tracking_id
                    }
                elif self.type == 'delivery':
                    data = {
                        'phone': phone,
                        'template_id': self.template_id.template_id,
                        'template_data': template_data,
                        'tracking_id': self.tracking_id
                    }
                self.data = data
                headers = {
                    'access_token': self.env['zalo.token'].search([('oa_id', '=', self.template_id.oa_id), (
                        'app_id', '=', self.template_id.app_id)]).access_token,
                    'Content-Type': 'application/json'
                }
                response = requests.post(url, data=json.dumps(data),
                                         headers=headers, verify=False)
                res = response.json()
                retry_times -= 2
                if res['error'] != 0:
                    self.mess_error = res['message']
                    self.state = 'error'
                elif res['error'] == 0:
                    sent_time = datetime.fromtimestamp(
                        float(res['data']['sent_time']) / 1000).strftime('%Y-%m-%d %H:%M:%S')
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

    def get_param_template_custom(self):
        try:
            template_data = {}

            customer_name = self.env['map.zns.config'].search(
                [('model', '=', 'zns.information'),
                 ('template_id', '=', self.template_id.template_id),
                 ('param_erp', '=', 'customer_name'),
                 ('active', '=', True)], limit=1)
            if customer_name and customer_name.param_zns in self.template_id.list_params.mapped(
                    'name'):
                template_data[customer_name.param_zns] = self.customer_name

            if self.type == 'sale_online':
                online_order_id = self.env['map.zns.config'].search(
                    [('model', '=', 'zns.information'),
                     ('template_id', '=', self.template_id.template_id),
                     ('param_erp', '=', 'online_order_id'), ('active', '=', True)], limit=1)
                if online_order_id and online_order_id.param_zns in self.template_id.list_params.mapped('name'):
                    template_data[online_order_id.param_zns] = self.order_code

                pos_name =  self.env['map.zns.config'].search(
                    [('model', '=', 'zns.information'),
                     ('template_id', '=', self.template_id.template_id),
                     ('param_erp', '=', 'pos_name'), ('active', '=', True)], limit=1)
                if pos_name and pos_name.param_zns in self.template_id.list_params.mapped('name'):
                    template_data[pos_name.param_zns] = self.shop_name

            elif self.type == 'waiting_delivery':
                pos_name = self.env['map.zns.config'].search(
                    [('model', '=', 'zns.information'),
                     ('template_id', '=', self.template_id.template_id),
                     ('param_erp', '=', 'pos_name'), ('active', '=', True)],
                    limit=1)
                if pos_name and pos_name.param_zns in self.template_id.list_params.mapped(
                        'name'):
                    template_data[pos_name.param_zns] = self.shop_name

                order_id = self.env['map.zns.config'].search(
                    [('model', '=', 'zns.information'),
                     ('template_id', '=', self.template_id.template_id),
                     ('param_erp', '=', 'order_id'),
                     ('active', '=', True)], limit=1)
                if order_id and order_id.param_zns in self.template_id.list_params.mapped(
                        'name'):
                    template_data[order_id.param_zns] = self.order_code

                order_value = self.env['map.zns.config'].search(
                    [('model', '=', 'zns.information'),
                     ('template_id', '=', self.template_id.template_id),
                     ('param_erp', '=', 'order_value'), ('active', '=', True)],
                    limit=1)
                if order_value and order_value.param_zns in self.template_id.list_params.mapped(
                        'name'):
                    template_data[order_value.param_zns] = self.order_value

            elif self.type == 'delivery':
                order_id = self.env['map.zns.config'].search(
                    [('model', '=', 'zns.information'),
                     ('template_id', '=', self.template_id.template_id),
                     ('param_erp', '=', 'order_id'),
                     ('active', '=', True)], limit=1)
                if order_id and order_id.param_zns in self.template_id.list_params.mapped(
                        'name'):
                    template_data[order_id.param_zns] = self.order_code

                minute = self.env['map.zns.config'].search(
                    [('model', '=', 'zns.information'),
                     ('template_id', '=', self.template_id.template_id),
                     ('param_erp', '=', 'minute'),
                     ('active', '=', True)], limit=1)
                if minute and minute.param_zns in self.template_id.list_params.mapped(
                        'name'):
                    template_data[minute.param_zns] = self.minute

            return template_data
        except Exception as e:
            raise ValidationError(e)


