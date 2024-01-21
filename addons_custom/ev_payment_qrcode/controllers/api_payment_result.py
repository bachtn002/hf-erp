# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import Controller, route, request
from ..helpers.Response import Response
from ..helpers import Configs
import hashlib
import hmac

class ApiCallbackQRCode(Controller):
    @route('/api/payment/result', methods=['GET'], type='http', auth='public')
    def api_payment_result(self):
        try:
            remote_ip = Configs.get_request_ip(request)
            is_ip_valid = Configs.check_allow_ip(remote_ip)
            params = request.params

            # Check HASH MAC SHA256
            dict_params = dict(params)

            payment_create_order_qrcode_res = request.env['payment.create.order.qrcode.res'].sudo().search(
                [('pg_order_reference', '=', dict_params['pg_order_reference'])], limit=1)
            if not payment_create_order_qrcode_res:
                mesg = _("PG_ORDER_REFERENCE_NOT_FOUND_FOR_HMAC_256")
                Configs._set_log_api(remote_ip, '/api/payment/result', 'Kết quả thanh toán qrcode', params, '400', mesg)
                return Response.error(mesg, data={}, code='400').to_json()
            
            dict_params.update({
                'session_id': payment_create_order_qrcode_res.session_id
            })

            filtered_data = {key: value for key, value in dict_params.items() if
                             value is not None and value != "" and key not in ["mac_type", "mac"]}
            sorted_data = sorted(filtered_data.items(), key=lambda x: x[0])
            query_string = "&".join(["{}={}".format(key, value) for key, value in sorted_data])
            secret_key = request.env['ir.config_parameter'].sudo().get_param('mbpay_hash_secret_key')

            # hash_mac_256 = hmac.new(secret_key.encode(), msg=query_string.encode(), digestmod=hashlib.sha256).hexdigest().upper()
            hash_mac_256 = hashlib.new('sha256')
            hash_mac_256.update(secret_key.encode())
            hash_mac_256.update(query_string.encode())
            hash_mac_value = hash_mac_256.hexdigest().upper()

            if hash_mac_value != dict_params['mac']:
                mesg = _("MAC_NOT_MATCH___ %s" % hash_mac_value)
                Configs._set_log_api(remote_ip, '/api/payment/result', 'Kết quả thanh toán qrcode', params, '400', mesg)
                return Response.error(mesg, data={}, code='400').to_json()

            if not is_ip_valid:
                mesg = _("YOUR_IP_ADDRESS_NOT_ALLOWED_TO_ACCESS_API")
                Configs._set_log_api(remote_ip, '/api/payment/result', 'Kết quả thanh toán qrcode', params, '400', mesg)
                return Response.error(mesg, data={}, code='400').to_json()

            val = {
                'ip_request': remote_ip,
                'response': str(dict(params)),
                'type': 'log_mb_payment_result',
            }
            callback_payment_log = request.env['callback.payment.log'].sudo().create(val)
            callback_payment_log.action_payment_qrcode_transaction()

            mesg = _('SUCCESS')
            Configs._set_log_api(remote_ip, '/api/payment/result', 'Kết quả thanh toán qrcode', params, '200', mesg)
            return Response.success(mesg, data={}).to_json()
        except Exception as ex:
            mesg = _('INTERNAL_SERVER_ERROR')
            return Response.error(str(ex), code='500').to_json()
