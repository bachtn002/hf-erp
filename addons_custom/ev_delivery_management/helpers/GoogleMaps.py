# -*- coding: utf-8 -*-

import googlemaps
from odoo.exceptions import ValidationError
from odoo import _
from odoo.http import request


def get_lat_long(address):
    api_key = request.env['ir.config_parameter'].sudo().get_param('google_maps_api_key')
    client = googlemaps.Client(api_key)
    response = client.geocode(address)
    if not response:
        raise ValidationError(_('The address "{}" is does not exits or not clear!').format(address))
    lat = response[0]['geometry']['location']['lat']
    long = response[0]['geometry']['location']['lng']

    return lat, long


def get_distance(address_1, address_2):
    api_key = request.env['ir.config_parameter'].sudo().get_param('google_maps_api_key')
    client = googlemaps.Client(api_key)
    response = client.distance_matrix(address_1, address_2)
    status = response.get('status')
    if status == 'OK':
        distance = response.get('rows')[0].get('elements')[0].get('distance').get('value') / 1000
        return distance
    else:
        raise ValidationError(_('Can not get distance, please check address received!'))
