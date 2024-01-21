import json
import math

import requests
from odoo import models
from odoo.exceptions import ValidationError
from ...ev_zalo_notification_service.helpers import APIGetToken

class DeliveryManagement(models.Model):
    _inherit = 'delivery.management'

    def write(self, vals):
        try:
            res = super(DeliveryManagement, self).write(vals)
            if self.order_id and self.order_id.pos_channel_id.is_allow_send_zns:
                if 'state' in vals and vals['state'] == 'done':
                    oa_id = self.store_id.x_oa_id
                    app_id = self.store_id.x_app_id
                    tmpl_id = self.store_id.x_template_id
                    template_id = self.env['zns.template'].sudo().search(
                        [('template_id', '=', tmpl_id), ('oa_id', '=', oa_id),
                         ('app_id', '=', app_id)],
                        limit=1)
                    type_send_id = self.env['type.send.zns'].sudo().search(
                        [('code', '=', 'erp_hf'), ('active', '=', True)],
                        limit=1)
                    if self.order_id.partner_id.phone and template_id:
                        value = {
                            'template_id': template_id.id,
                            'type': 'order',
                            'type_send_id': type_send_id.id,
                            'order_id': self.order_id.id,
                            'order_code': self.order_id.pos_reference,
                            'order_date': self.order_id.date_order,
                            'phone': self.order_id.partner_id.phone,
                            'customer_name': self.order_id.partner_id.name,
                            'order_value': self.order_id.amount_total,
                            'point_plus': self.order_id.loyalty_points,
                            'point_value': self.order_id.partner_id.loyalty_points,
                            'shop_id': self.store_id.id,
                            'shop_name': self.store_id.name,
                        }
                        zns_information = self.env[
                            'zns.information'].sudo().create(value)
                        zns_information.action_send_zns()

                if 'state' in vals and vals['state'] == 'delivering':
                    res_partner_zalo = self.env['res.partner.zalo'].search(
                        [('phone', '=', self.order_id.partner_id.phone)], limit=1)
                    distance = self.distance
                    minute = 10
                    if distance > 3:
                        minute += 2 * math.ceil(distance - 3)

                    order_code = self.order_id.sale_online + '/' + self.order_id.pos_reference if self.order_id.sale_online else self.order_id.pos_reference

                    if res_partner_zalo:
                        zalo_id = res_partner_zalo.zalo_id
                        oa_id = res_partner_zalo.oa_id
                        app_id = res_partner_zalo.app_id

                        self.env[
                            'data.webhook.zns'].send_message_notify_delivery(
                            zalo_id, oa_id, app_id,
                            self.order_id.partner_id.name,
                            order_code, minute, self.track_url)
                    else:
                        self.send_zns_notify_delivery(order_code, minute)
            return res
        except Exception as e:
            raise ValidationError(e)

    def send_zns_notify_delivery(self, order_code, minute):
        template = self.env['zns.template'].search(
            [('template_type', '=', 'order_delivery'),
             ('status', '=', 'enable')], limit=1)
        type_send_id = self.env['type.send.zns'].sudo().search(
            [('code', '=', 'erp_hf'), ('active', '=', True)], limit=1)
        val = {
            'template_id': template.id,
            'type': 'delivery',
            'type_send_id': type_send_id.id,
            'order_id': self.order_id.id,
            'order_code': order_code,
            'order_date': self.order_id.date_order,
            'phone': self.order_id.partner_id.phone,
            'customer_name': self.order_id.partner_id.name,
            'order_value': self.order_id.amount_total,
            'point_plus': self.order_id.loyalty_points,
            'point_value': self.order_id.partner_id.loyalty_points,
            'shop_id': self.store_id.id,
            'shop_name': self.store_id.name,
            'minute': minute
        }
        zns_information = self.env['zns.information'].sudo().create(val)
        zns_information.action_send_zns_sale_online()
