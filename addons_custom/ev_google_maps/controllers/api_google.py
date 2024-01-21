# -*- coding: utf-8 -*-
import logging
import requests
import json
import googlemaps

from odoo import http, _
from odoo.http import request

from ..helpers import GoogleMaps

_logger = logging.getLogger(__name__)


class GoogleMapsAPI(http.Controller):

    @http.route('/maps/lat_long', methods=['POST'], type='json', auth='public')
    def set_lat_long(self):
        params = request.params
        id = params['id'] if 'id' in params else False
        model = params['model'] if 'model' in params else False
        lat = params['lat'] if 'lat' in params else False
        long = params['long'] if 'long' in params else False
        address = params['address'] if 'address' in params else False
        if id and model and lat and long and address:
            result = request.env[model].sudo().search([('id', '=', id)], limit=1)
            if result:
                result.set_lat_long(lat, long, address)
                return "return lat long"

    @http.route('/maps/distance', methods=['POST'], type='json', auth='public')
    def set_distance(self):
        params = request.params
        pos_config_id = params['id'] if 'id' in params else False
        api_key = request.env['ir.config_parameter'].sudo().get_param('google_maps_api_key')
        client = googlemaps.Client(api_key)
        pos_shop = request.env['pos.config'].sudo().search([('id', '=', int(pos_config_id))], limit=1).x_pos_shop_id
        address_1 = pos_shop.address
        address_2 = params['address'] if 'address' in params else False
        response = client.distance_matrix(address_1, address_2)
        status = response['status']
        if status == 'OK':
            distance = ((response['rows'][0]['elements'][0]['distance']['text']))
            return distance
        else:
            return "False"
