# -*- coding: utf-8 -*-
import googlemaps
from odoo.http import request
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError



from ..helpers import GoogleMaps


class SaleOnline(models.Model):
    _inherit = 'sale.online'

    x_pos_lat = fields.Char('Pos Lat')
    x_pos_long = fields.Char('Pos Long')
    x_distance = fields.Float('Distance Delivery', digits=(12,3))
    is_pos_config_changed = fields.Char('Pos Lat')

    @api.onchange('x_pos_lat', 'x_pos_long')
    def _update_lat_long(self):
        self.lat = self.x_pos_lat
        self.long = self.x_pos_long

    def get_condition_searchbox(self):
        if self.state != 'draft':
            return False
        return True

    def send_sale_request(self):
        try:
            if self.home_delivery:
                pos_shop = self.pos_config_id.x_pos_shop_id
                if not pos_shop.address or not pos_shop.phone or not pos_shop.lat or not pos_shop.long:
                    raise UserError(
                        _('You cannot submit a home delivery order with a point of sale that lacks delivery information. Please contact your administrator!'))

            return super(SaleOnline, self).send_sale_request()
        except Exception as e:
            raise ValidationError(e)

    @api.onchange('home_delivery')
    def onchange_home_delivery(self):
        if not self.home_delivery:
            self.receiver = False 
            self.receiver_phone = False
            self.x_distance = False
            self.address_delivery = False
            self.lat = False
            self.long = False
        else:
            pos_shop = self.pos_config_id.x_pos_shop_id
            if not pos_shop.address or not pos_shop.phone or not pos_shop.lat or not pos_shop.long:
                raise UserError(
                    _('You cannot submit a home delivery order with a point of sale that lacks delivery information. Please contact your administrator!'))
            if self.customer:
                self.receiver = self.customer
            if self.phone:
                self.receiver_phone = self.phone

    @api.onchange('address_delivery')
    def _get_distance_delivery(self):
        try:
            if self.pos_config_id:
                pos_shop_id = self.pos_config_id.x_pos_shop_id
                if self.lat and self.long and pos_shop_id.lat and pos_shop_id.long:
                    lat_long1 = pos_shop_id.lat + ',' + pos_shop_id.long
                    lat_long2 = self.lat + ',' + self.long
                    self.get_x_distance_delivery(lat_long1, lat_long2)
        except Exception as e:
            raise ValidationError(e)

    @api.onchange('customer', 'phone')
    def _get_detail_receiver(self):
        try:
            if self.home_delivery:
                if self.customer:
                    self.receiver = self.customer
                if self.phone:
                    self.receiver_phone = self.phone
        except Exception as e:
            raise ValidationError(e)
    
    @api.onchange('pos_config_id')
    def _get_pos_lat_long(self):
        try:
            if self.pos_config_id:
                pos_shop_id = self.pos_config_id.x_pos_shop_id
                # recompute distance when config changes
                if self.lat and self.long and pos_shop_id.lat and pos_shop_id.long:
                    lat_long1 = pos_shop_id.lat + ',' + pos_shop_id.long
                    lat_long2 = self.lat + ',' + self.long
                    self.get_x_distance_delivery(lat_long1, lat_long2)
                if pos_shop_id.lat and pos_shop_id.long:
                    # field help to get lat long default based on shop and show default marker on maps
                    self.is_pos_config_changed = pos_shop_id.lat + ',' + pos_shop_id.long
                if not pos_shop_id.lat or not pos_shop_id.long:
                    self.is_pos_config_changed = False
                    self.home_delivery = False
        except ValidationError as e:
            raise ValidationError(e)
    
    def get_x_distance_delivery(self, lat_long1, lat_long2):
        try:
            api_key = request.env['ir.config_parameter'].sudo().get_param('google_maps_api_key')
            client = googlemaps.Client(api_key)
            response = client.distance_matrix(lat_long1, lat_long2)
            status = response['status']
            if status == 'OK':
                distance_raw = ((response['rows'][0]['elements'][0]['distance']['text'].split(' ')))
                distance = float(distance_raw[0])
                if distance_raw[1] == 'm':
                    distance = (distance * 0.001)
                self.x_distance = (distance)
            else:
                self.x_distance = "FALSE"
        except Exception as e:
            raise ValidationError(e)

    def set_lat_long(self, lat, long, address):
        try:
            self.lat = lat
            self.long = long
            self.address_delivery = address
        except Exception as e:
            raise ValidationError(e)

    @api.model
    def sync_orders_online(self, config_id, fields):
        order_ids = self.env['sale.online'].search([('pos_config_id', '=', config_id), ('state', '=', 'sent')])
        orders = []

        for order in order_ids:
            lines = []
            for line in order.order_line_ids:
                product = self.env['product.product'].search_read(domain=[('product_tmpl_id', '=', line.product_id.id)],
                                                                  fields=fields)
                product_id = self.env['product.product'].search([('product_tmpl_id', '=', line.product_id.id)], limit=1)
                product_combos = self.env['product.combo'].search([('product_tmpl_id', '=', line.product_id.id)])
                line = {
                    'product_id': product_id.id,
                    'price': line.price,
                    'amount': line.amount,
                    'uom': line.uom.id,
                    'product_uom_category_id': line.product_uom_category_id.id,
                    'quantity': line.quantity,
                    'sale_online_id': line.sale_online_id.id,
                    'product': product,
                }
                lines.append(line)
                # nếu sp online là combo thì load thêm thành phần
                if len(product_combos) > 0:
                    for product in product_combos:
                        line = {
                            'product_id': product.product_ids.id,
                            'quantity': product.no_of_items,
                            'product': product.product_ids,
                            'product_combo_parent': product.product_tmpl_id.id
                        }
                        lines.append(line)
                # line = {
                #     'product_id': product_id.id,
                #     'price': line.price,
                #     'amount': line.amount,
                #     'uom': line.uom.id,
                #     'product_uom_category_id': line.product_uom_category_id.id,
                #     'quantity': line.quantity,
                #     'sale_online_id': line.sale_online_id.id,
                #     'product': product,
                # }
                # lines.append(line)
            partner = False
            if order.partner_id.id != False:
                partner_groups = []
                for group in order.partner_id.partner_groups:
                    partner_groups.append(group.id)
                partner = {
                    'id': order.partner_id.id,
                    'name': order.partner_id.name,
                    'street': order.partner_id.street,
                    'city': order.partner_id.city,
                    'state_id': False,
                    'country_id': False,
                    'vat': False,
                    'lang': False,
                    'phone': order.partner_id.phone,
                    'zip': False,
                    'mobile': False,
                    'email': order.partner_id.email,
                    'barcode': order.partner_id.barcode,
                    'write_date': order.partner_id.write_date,
                    'property_account_position_id': False,
                    'property_product_pricelist': False,
                    'loyalty_points': order.partner_id.loyalty_points,
                    'partner_groups': partner_groups,
                }
            _order = {
                'name': order.name,
                'date': order.date,
                'pos_config_id': order.pos_config_id.id,
                'price_list_id': order.price_list_id.id,
                'order_line_ids': lines,
                'customer': order.customer,
                'phone': order.phone,
                'address': order.address,
                'note': order.note,
                'home_delivery': order.home_delivery,
                'address_delivery': order.address_delivery,
                'receiver': order.receiver,
                'receiver_phone': order.receiver_phone,
                'x_distance': order.x_distance,
                'lat': order.lat,
                'long': order.long,
                'partner': partner,
                'source_order_id': order.source_order_id.id
            }
            orders.append(_order)
        return orders