# -*- coding: utf-8 -*-
import re

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

from ..helpers import GoogleMaps


class StockTransfer(models.Model):
    _inherit = 'stock.transfer'

    x_ship_type = fields.Selection([('no', 'No'), ('internal', 'Internal'), ('other', 'Other')], 'Ship type',
                                   default='no')
    x_driver = fields.Selection([('out', 'Out'), ('in', 'In')], 'Warehouse Ship', default='out')

    # def action_choose_out_date(self):
    #     try:
    #         res = super(StockTransfer, self).action_choose_out_date()
    #         if self.x_ship_type != 'no':
    #             if self.x_ship_type == 'other' and not self.company_id.x_call_ship:
    #                 raise UserError(_('The system does not allow calling to ship outside'))
    #             self.action_create_delivery()
    #         return res
    #     except Exception as e:
    #         raise ValidationError(e)

    def action_create_delivery(self):
        try:
            shop_sender = self.env['pos.shop'].sudo().search([('warehouse_id', '=', self.warehouse_id.id)], limit=1)
            phone_sender = re.sub(r"[^0-9]", "", shop_sender.phone) if shop_sender else None
            shop_recipient = self.env['pos.shop'].sudo().search([('warehouse_id', '=', self.warehouse_dest_id.id)],
                                                                limit=1)
            phone_recipient = re.sub(r"[^0-9]", "", shop_recipient.phone) if shop_recipient else None
            ship_internal_id = self.env['delivery.partner'].sudo().search([('code', '=', 'internal')], limit=1)
            from_address = (shop_sender.lat, shop_sender.long)
            to_address = (shop_recipient.lat, shop_recipient.long)
            if self.x_driver == 'in' and self.x_ship_type == 'internal':
                distance = GoogleMaps.get_distance(from_address, to_address)
            else:
                distance = GoogleMaps.get_distance(to_address, from_address)
            data = {
                'origin': self.name,
                'type_origin': 'transfer',
                'store_id': shop_sender.id,
                # 'ship_type': 'internal',
                'is_delivery_internal': True if self.x_ship_type == 'internal' else False,
                'delivery_partner_id': ship_internal_id.id if self.x_ship_type == 'internal' else None,
                'delivery_fee': 0,
                'total_price': 0,
                'transfer_id': self.id,
                'distance': round(distance, 1),

                'height': 20,
                'width': 20,
                'depth': 20,
                'weight': 5,

                'sender_id': self.write_uid.partner_id.id,
                'phone_sender': phone_sender,
                'address_sender': shop_sender.address,
                'lat_sender': shop_sender.lat,
                'long_sender': shop_sender.long,

                'recipient_id': shop_recipient.name,
                'phone_recipient': phone_recipient,
                'address_recipient': shop_recipient.address,
                'lat_recipient': shop_recipient.lat,
                'long_recipient': shop_recipient.long,

                'description': '',
            }
            if self.x_driver == 'in' and self.x_ship_type == 'internal':
                create_uid = self.env['stock.request'].sudo().search([('stock_transfer_id', '=', self.id)], limit=1)

                data = {
                    'origin': self.name,
                    'type_origin': 'transfer',
                    'store_id': shop_recipient.id,
                    # 'ship_type': 'internal',
                    'is_delivery_internal': True if self.x_ship_type == 'internal' else False,
                    'delivery_partner_id': ship_internal_id.id if self.x_ship_type == 'internal' else None,
                    'delivery_fee': 0,
                    'total_price': 0,
                    'transfer_id': self.id,
                    'distance': round(distance, 1),

                    'height': 20,
                    'width': 20,
                    'depth': 20,
                    'weight': 5,

                    'sender_id': create_uid.create_uid.partner_id.id,
                    'phone_sender': phone_recipient,
                    'address_sender': shop_recipient.address,
                    'lat_sender': shop_recipient.lat,
                    'long_sender': shop_recipient.long,

                    'recipient_id': shop_sender.name,
                    'phone_recipient': phone_sender,
                    'address_recipient': shop_sender.address,
                    'lat_recipient': shop_sender.lat,
                    'long_recipient': shop_sender.long,

                    'description': '',
                }
            delivery_id = self.env['delivery.management'].sudo().create(data)
            delivery_id.action_send()
            return
        except Exception as e:
            raise ValidationError(e)
