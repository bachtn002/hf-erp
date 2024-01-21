# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from odoo import models
from odoo.exceptions import ValidationError


class ZNSInformation(models.Model):
    _inherit = 'zns.information'

    def get_param_template(self):
        try:
            template_data = {}

            order_code = self.env['map.zns.config'].search(
                [('model', '=', 'zns.information'), ('template_id', '=', self.template_id.template_id),
                 ('param_erp', '=', 'order_code'), ('active', '=', True)], limit=1)
            if order_code and order_code.param_zns in self.template_id.list_params.mapped('name'):
                template_data[order_code.param_zns] = self.order_code

            order_date = self.env['map.zns.config'].search(
                [('model', '=', 'zns.information'), ('template_id', '=', self.template_id.template_id),
                 ('param_erp', '=', 'order_date'), ('active', '=', True)], limit=1)
            if order_date and order_date.param_zns in self.template_id.list_params.mapped('name'):
                date = datetime.strftime(self.order_date + timedelta(hours=7), '%H:%M %d/%m/%Y')
                template_data[order_date.param_zns] = date

            customer_name = self.env['map.zns.config'].search(
                [('model', '=', 'zns.information'), ('template_id', '=', self.template_id.template_id),
                 ('param_erp', '=', 'customer_name'), ('active', '=', True)], limit=1)
            if customer_name and customer_name.param_zns in self.template_id.list_params.mapped('name'):
                template_data[customer_name.param_zns] = self.customer_name

            order_value = self.env['map.zns.config'].search(
                [('model', '=', 'zns.information'), ('template_id', '=', self.template_id.template_id),
                 ('param_erp', '=', 'order_value'), ('active', '=', True)], limit=1)
            if order_value and order_value.param_zns in self.template_id.list_params.mapped('name'):
                template_data[order_value.param_zns] = self.order_value

            point_plus = self.env['map.zns.config'].search(
                [('model', '=', 'zns.information'), ('template_id', '=', self.template_id.template_id),
                 ('param_erp', '=', 'point_plus'), ('active', '=', True)], limit=1)
            if point_plus and point_plus.param_zns in self.template_id.list_params.mapped('name'):
                template_data[point_plus.param_zns] = self.point_plus

            point_value = self.env['map.zns.config'].search(
                [('model', '=', 'zns.information'), ('template_id', '=', self.template_id.template_id),
                 ('param_erp', '=', 'point_value'), ('active', '=', True)], limit=1)

            if point_value and point_value.param_zns in self.template_id.list_params.mapped('name'):
                template_data[point_value.param_zns] = self.point_value

            shop_name = self.env['map.zns.config'].search(
                [('model', '=', 'zns.information'), ('template_id', '=', self.template_id.template_id),
                 ('param_erp', '=', 'shop_name'), ('active', '=', True)], limit=1)
            if shop_name and shop_name.param_zns in self.template_id.list_params.mapped('name'):
                template_data[shop_name.param_zns] = self.shop_name

            return template_data
        except Exception as e:
            raise ValidationError(e)

    def data_order_zns(self):
        try:

            phone = '84' + self.phone.lstrip('0')

            template_data = self.get_param_template()
            data = {
                'type_send_zns': self.type_send_id.code,
                'authentication': self.type_send_id.token,
                'data': {
                    'phone': phone,
                    'template_id': self.template_id.template_id,
                    'template_data': template_data
                }

            }
            return data
        except Exception as e:
            raise ValidationError(e)
