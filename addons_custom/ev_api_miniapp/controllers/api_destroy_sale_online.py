# -*- coding: utf-8 -*-

from odoo.addons.ev_config_connect_api.helpers import Configs
from odoo.addons.ev_config_connect_api.helpers.Response import Response
from odoo.http import Controller, route, request


def res(remote_ip=None, data=None, params=None, msg=None):
    Configs._set_log_api(remote_ip, '/sale_online/cancel', 'Hủy đơn online miniapp', params, '400', msg)
    return Response.error(msg, data, code='400').to_json()


class ApiDestroySaleOnline(Controller):
    @route('/sale_online/cancel', methods=['POST'], type='json', auth='public', cors='*', csrf=False)
    def api_destroy_sale_online(self):
        params = request.params
        remote_ip = Configs.get_request_ip()
        is_ip_valid = Configs.check_allow_ip(remote_ip)
        if not is_ip_valid:
            msg = 'YOUR_IP_ADDRESS_NOT_ALLOWED_TO_ACCESS_API'
            return res(remote_ip, None, params, msg)
        if 'token_connect_api' not in params or not params['token_connect_api']:
            msg = 'TOKEN_CONNECT_API_INVALID'
            return res(remote_ip, None, params, msg)
        api_config = Configs._get_api_config(params['token_connect_api'])
        if not api_config:
            msg = 'TOKEN_CONNECT_API_INVALID'
            return res(remote_ip, None, params, msg)
        try:
            ref_order = params['ref_order']
            if not ref_order:
                return res(remote_ip, None, params, msg='INVALID_REF_ORDER')
            reason = params['reason']
            sale_online = request.env['sale.online'].sudo().search(
                [('ref_order', '=', ref_order), ('state', 'not in', ('cancel', 'finish'))])
            if not sale_online:
                return res(remote_ip, None, params, msg='INVALID_REF_ORDER')
            for i in sale_online:
                i.cancel_reason = reason
                i.cancel_sale_online()
            Configs._set_log_api(remote_ip, '/sale_online/cancel', 'Hủy đơn online miniapp', params, '200', None)
            return Response.success(None, data={'sale_online_ids': sale_online.ids}).to_json()
        except Exception as ex:
            msg = 'INTERNAL_SERVER_ERROR'
            Configs._set_log_api(remote_ip, '/sale_online/cancel', 'Hủy đơn online miniapp', params, '500', str(ex))
            return Response.error(message=msg, data={'message_error': str(ex)}, code='500').to_json()
