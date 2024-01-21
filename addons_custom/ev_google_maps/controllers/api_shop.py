# -*- coding: utf-8 -*-
import logging

import requests
import json

from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError

from ..helpers import Response, GoogleMaps

_logger = logging.getLogger(__name__)


class APIShop(http.Controller):

    @http.route('/shop/get_detail', methods=['GET'], type='http', auth='public')
    def get_shop_detail(self):
        auth = request.env['ir.config_parameter'].sudo().get_param('authorization_internal')
        authorization = request.httprequest.headers.get('Authorization')
        if authorization == auth:
            shop_ids = request.env['pos.shop'].sudo().search([], order='id asc')
            if shop_ids:
                def __get_data():
                    for shop in shop_ids:
                        yield {
                            'id': shop.id,
                            'code': shop.code,
                            'name': shop.name,
                            'address': shop.address,
                            'country_state': shop.country_state_id.name,
                            'lat': shop.lat,
                            'long': shop.long,
                        }
                return Response.Response.success('Success',
                                                 data={
                                                     "record_total": len(shop_ids),
                                                     "data": list(__get_data()),
                                                 }).to_json()
            else:
                return Response.Response.success('No shop exists', code='204').to_json()
        else:
            return Response.Response.error('Authorization false', code='401').to_json()
