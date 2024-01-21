# -*- coding: utf-8 -*-
import logging
from odoo import http, _
from odoo.http import request

from ..helpers import Response, APIInternal

_logger = logging.getLogger(__name__)


class InternalAPI(http.Controller):

    @http.route('/internal/webhook', methods=['POST'], type='json', auth='public')
    def internal_webhook(self):

        authorization = request.httprequest.headers.environ['HTTP_AUTHORIZATION']
        client_secret = request.env['ir.config_parameter'].sudo().get_param('authorization_internal')
        if authorization != client_secret:
            data = {'code': 401, 'message': 'Authorization failed!'}
            return data

        params = request.jsonrequest
        delivery_id = request.env['delivery.management'].sudo().search([('name', '=', params['orderNo'])],

                                                                       limit=1)
        delivery = APIInternal.get_delivery_status(delivery_id)
        if delivery:
            delivery_id.state_delivery = delivery
            if delivery == 'WAITING':
                delivery_id.state = 'waiting'
            if delivery == 'PROCESSING':
                delivery_id.state = 'delivering'
            if delivery == 'DELIVERY_SUCCESS':
                delivery_id.state = 'done'
            if delivery == 'CANCELLED':
                delivery_id.state = 'cancel'
                delivery_id.failed_reason = params['failedReason'] if 'failedReason' in params else ''
            if delivery == 'DELIVERY_FAIL':
                delivery_id.state = 'cancel'
                delivery_id.failed_reason = params['failedReason'] if 'failedReason' in params else ''

    @http.route('/delivery/cancel_order', methods=['POST'], type='json', auth='public')
    def cancel_order_interal(self):

        authorization = request.httprequest.headers.environ['HTTP_AUTHORIZATION']
        client_secret = request.env['ir.config_parameter'].sudo().get_param('authorization_internal')
        if authorization != client_secret:
            data = {'code': 401, 'message': 'Authorization failed!'}
            return data

        params = request.jsonrequest
        delivery_id = request.env['delivery.management'].sudo().search([('name', '=', params['orderNo'])],
                                                                       limit=1)
        if delivery_id.state in ('draft', 'queue', 'waiting', 'delivering'):
            delivery_id.state = 'cancel'
            data = {'code': 200, 'success': 'True', 'message': 'Hủy đơn hàng thành công'}
        elif delivery_id.state == 'done':
            data = {'code': 202, 'success': 'False', 'message': 'Không thể hủy bỏ khi đơn hàng đang được xử lý'}
        else:
            data = {'code': 400, 'success': 'False', 'message': 'orderNo does not exits'}
        return data
