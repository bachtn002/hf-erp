# -*- coding: utf-8 -*-

import googlemaps


from odoo.http import request


def get_lat_long(address):
    api_key = request.env['ir.config_parameter'].sudo().get_param('google_maps_api_key')
    client = googlemaps.Client(api_key)
    response = client.geocode(address)
    lat = response[0]['geometry']['location']['lat']
    long = response[0]['geometry']['location']['lng']

    return lat, long
