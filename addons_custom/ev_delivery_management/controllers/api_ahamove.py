# -*- coding: utf-8 -*-
from odoo import http, _
import logging
from odoo.http import request

_logger = logging.getLogger(__name__)


class APIAhamove(http.Controller):

    @http.route('/ahamove/webhook', methods=['POST'], type='json', auth='public', csrf=False)
    def ahamove_webhook(self):
        # json_data = request.jsonrequest
        params = request.jsonrequest
        webhook_aha_id = request.env['webhook.aha'].sudo().create({'data': params})
        webhook_aha_id.action_confirm()
        # delivery_reference = json_data.get('_id')
        # phone = json_data.get('supplier_id')
        # driver_name = json_data.get('supplier_name')
        # status = json_data.get('status')
        # sub_status = json_data.get('path')[1].get('status') if json_data.get('path')[1].get('status') else ''
        # status_type = json_data.get('sub_status')
        # delivery_id = request.env['delivery.management'].sudo().search(
        #     [('delivery_reference', '=', delivery_reference)], limit=1)
        # if delivery_id:
        #     delivery_id.driver_name = driver_name
        #     delivery_id.driver_phone = phone
        #     delivery_id.license_plate = phone
        #     state = delivery_id.set_state_ahamove(status, sub_status, status_type)
        #     delivery_id.state = state
        #     delivery_id.state_delivery = status_type + ' | ' + status + ' | ' + sub_status
