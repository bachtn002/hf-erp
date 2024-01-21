# -*- coding: utf-8 -*-
import logging

from odoo import http, tools, _
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

from ..helpers import Configs
from ..helpers.Response import Response


class UpdatePromotionPhone(http.Controller):

    @http.route('/update_phone_code', methods=['POST'], type='json', auth='public')
    def get_update_phone_code(self):
        # Check connection and token to make valid connection
        params = http.request.params

        remote_ip = Configs.get_request_ip()
        # Check IP access in whitelist
        # is_ip_valid = Configs.check_allow_ip(remote_ip)
        #
        # if not is_ip_valid:
        #     mesg = _("Your ip address is not allowed to access this API. Contact to your Admin!")
        #     Configs._set_log_api(remote_ip, '/update_phone_code', '', params, '400', mesg)
        #     return Response.error(mesg, data={}, code='400').to_json()

        if 'token_connect_api' not in params:
            mesg = _("Missing token connection code!")
            Configs._set_log_api(remote_ip, '/update_phone_code', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()
        if 'promotion_code' not in params:
            mesg = _("Missing promotion code!")
            Configs._set_log_api(remote_ip, '/update_phone_code', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()
        elif not params['phone_number'].isnumeric():
            mesg = _("Phone number code invalid")
            Configs._set_log_api(remote_ip, '/update_phone_code', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()
        if 'phone_number' not in params:
            mesg = _("Missing phone number!")
            Configs._set_log_api(remote_ip, '/update_phone_code', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()
        if 'apply_condition' not in params:
            mesg = _("Missing apply condition!")
            Configs._set_log_api(remote_ip, '/update_phone_code', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        token = params['token_connect_api']

        api_id = Configs._get_api_config(token)

        if not api_id:
            mesg = _("Token connection invalid!")
            Configs._set_log_api(remote_ip, '/update_phone_code', '', params, '401', mesg)
            return Response.error(mesg, data={}, code='401').to_json()
        else:
            try:
                sync_log = request.env['sync.update.phone.code'].sudo().create({
                    'phone': params['phone_number'],
                    'promotion_code': params['promotion_code'],
                    'apply_condition': params['apply_condition'],
                    'token_connect_api': params['token_connect_api'],
                    'remote_ip': remote_ip,
                })
                sync_log.action_sync_promotion_code()
                mesg = _('Pos data successfully!')
                Configs._set_log_api(remote_ip, api_id.code, api_id.name, params, '200', mesg)
                return Response.success(mesg, data={}).to_json()
            except Exception as e:
                Configs._set_log_api(remote_ip, api_id.code, api_id.name, params, '504', e)
                return Response.error(str(e), data={}).to_json()
