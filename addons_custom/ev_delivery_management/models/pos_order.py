# -*- coding: utf-8 -*-
import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def create_from_ui(self, orders, draft=False):
        try:
            order_ids = super(PosOrder, self).create_from_ui(orders, draft)
            for order in self.sudo().browse([o['id'] for o in order_ids]):
                if not order.x_home_delivery:
                    continue
                if not order.partner_id:
                    continue
                if not order.x_pos_shop_id.lat and not order.x_pos_shop_id.long:
                    continue
                if not order.x_pos_shop_id.phone and not order.x_pos_shop_id.address:
                    continue
                phone = re.sub(r"[^0-9]", "", order.x_pos_shop_id.phone)
                ship_internal_id = self.env['delivery.partner'].sudo().search(
                    [('code', '=', 'internal'), ('active', '=', True)], limit=1)
                data = {
                    'origin': order.pos_reference,
                    'type_origin': 'order',
                    'store_id': order.x_pos_shop_id.id,
                    'delivery_partner_id': ship_internal_id.id if order.x_ship_type == 'internal' else None,
                    'is_delivery_internal': True if order.x_ship_type == 'internal' else False,
                    'delivery_fee': 0,
                    'cod': order.x_cod,
                    'total_price': order.amount_total,
                    'order_id': order.id,


                    'height': 20,
                    'width': 20,
                    'depth': 20,
                    'weight': 5,
                    'distance': order.x_distance,

                    'sender_id': order.create_uid.partner_id.id,
                    'phone_sender': phone,
                    'address_sender': order.x_pos_shop_id.address,
                    'lat_sender': order.x_pos_shop_id.lat,
                    'long_sender': order.x_pos_shop_id.long,

                    'recipient_id': order.x_receiver,
                    'phone_recipient': order.x_partner_phone,
                    'address_recipient': order.x_address_delivery,
                    'lat_recipient': order.x_lat,
                    'long_recipient': order.x_long,

                    'description': order.x_ship_note,
                }
                delivery_id = self.env['delivery.management'].create(data)
                delivery_id.action_send()
            return order_ids
        except Exception as e:
            raise ValidationError(e)
