# -*- coding: utf-8 -*-
import logging

import requests
import json

from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError

from ..helpers import APIGrab, Response, GoogleMaps

_logger = logging.getLogger(__name__)


class GrabAPI(http.Controller):

    @http.route('/grab/webhook', methods=['POST'], type='json', auth='public')
    def grab_webhook(self):
        # authorization = request.httprequest.headers.environ['HTTP_AUTHORIZATION']
        # # client_id = request.env['ir.config_parameter'].sudo().get_param('client_grab_id')
        # client_secret = request.env['ir.config_parameter'].sudo().get_param('client_grab_secret')
        # if authorization != client_secret:
        #     msg = _('Authorization False')
        #     return Response.Response.error(msg, code='401', ).to_json()

        params = request.jsonrequest
        webhook_grab_id = request.env['webhook.grab'].sudo().create({'data': params})
        webhook_grab_id.action_confirm()
        # delivery_id = request.env['delivery.management'].sudo().search([('name', '=', params.get('merchantOrderID'))],
        #                                                                limit=1)
        # if delivery_id:
        #     delivery_id.state_delivery = params.get('status')
        #     delivery_id.track_url = params.get('trackURL')
        #     delivery_id.pickup_pin = params.get('pickupPin')
        #     delivery_id.driver_name = params.get('driver').get('name')
        #     delivery_id.driver_phone = params.get('driver').get('phone')
        #     delivery_id.license_plate = params.get('driver').get('licensePlate')
        #     delivery_id.failed_reason = params.get('failedReason')
        #     if params.get('status') == 'PICKING_UP':
        #         delivery_id.state = 'pickup'
        #     if params.get('status') == 'IN_DELIVERY':
        #         delivery_id.state = 'delivering'
        #     if params.get('status') in ('COMPLETED', 'RETURNED'):
        #         delivery_id.state = 'done'
        #     if params.get('status') == 'FAILED':
        #         delivery_id.state = 'failed'
        #         # delivery_id.failed_reason = params['failedReason'] if 'failedReason' in params else ''
        #     if params.get('status') == 'RETURNED':
        #         delivery_id.state = 'received'
        #     if params.get('status') == 'ALLOCATING':
        #         delivery_id.state = 'waiting'
        #         delivery_id.driver_name = None
        #         delivery_id.driver_phone = None
        #         delivery_id.license_plate = None
        #         delivery_id.track_url = None
