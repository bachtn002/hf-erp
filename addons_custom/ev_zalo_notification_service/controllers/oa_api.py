# -*- coding: utf-8 -*-
import logging
import requests
import json

from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError

from ..helpers import APIGetToken, APIZNS, Connection
from ..helpers.Response import Response

from datetime import datetime, date

_logger = logging.getLogger(__name__)


class ZaloOfficialAccountAPI(http.Controller):

    # @http.route('/zalo_oa/authorization_code', methods=['GET'], type='http', auth='public')
    # def get_authorization_code(self):
    #     try:
    #         APIZNS.get_profile("8474538440307653240")
    #         # params = request.params
    #         # auth_code = params['code']
    #         # oa_id = params['oa_id']
    #         # APIGetToken.get_access_token_by_auth_code(oa_id, auth_code)
    #     except Exception as e:
    #         raise ValidationError(e)

    @http.route('/zalo_oa/webhook', methods=['POST'], type='json', auth='public')
    def zalo_oa_webhook(self):
        try:
            data = request.jsonrequest
            # event_name = data.get('event_name')
            # if event_name == 'user_send_text':
            data = {
                'data': data,
            }
            data_id = request.env['data.webhook.zns'].create(data)
            data_id.action_confirm()
            return {'code': 200}
        except Exception as e:
            raise ValidationError(e)

    @http.route('/zalo_oa/access_token', methods=['Post'], type='json', auth='public')
    def send_access_token(self):
        try:

            oa_id = request.jsonrequest.get('oa_id')
            app_id = request.jsonrequest.get('app_id')
            secret_key = request.jsonrequest.get('secret_key')

            oa_id = request.env['zalo.official.account'].sudo().search(
                [('oa_id', '=', oa_id), ('app_id', '=', app_id), ('secret_key', '=', secret_key)],
                order='create_date desc', limit=1)
            if not oa_id:
                msg = _("Incorrect oa id or app_id")
                return Response.error(msg, code='400').to_json()

            zalo_token = self.get_zalo_token(oa_id, app_id)
            zalo_token_check = request.env['zalo.token']
            if type(zalo_token) == type(zalo_token_check):
                data = {
                    'access_token': zalo_token.access_token,
                    'refresh_token': zalo_token.refresh_token,
                    'expires_access_token': zalo_token.expires_access_token,
                    'expires_refresh_token': zalo_token.expires_refresh_token,
                }
                return Response.success('Success', data=data).to_json()
            else:
                return Response.error(zalo_token, code='400').to_json()
        except Exception as e:
            raise ValidationError(e)

    @http.route('/zalo_oa/send_message', methods=['POST'], type='json', auth='public')
    def send_message(self):
        try:
            # check ip được phép truy cập
            remote_ip = Connection.get_request_ip()
            is_ip_valid = Connection.check_allow_ip(remote_ip)
            if not is_ip_valid:
                mesg = _('Your ip address is not allowed to access this API. Contact to your Admin!')
                return Response.error(mesg, data={}, code='400').to_json()
            params = request.jsonrequest
            authentication = params['authentication']
            type_send_zns = params['type_send_zns']

            # check được phép gửi tin zns
            type_send = request.env['type.send.zns'].sudo().search(
                [('code', '=', type_send_zns), ('token', '=', authentication), ('active', '=', True)], limit=1)
            if not type_send:
                msg = _('You are not allowed to send messages zns!')
                return Response.error(msg, code='400').to_json()

            oa_id = params.get('oa_id')
            app_id = params.get('app_id')
            zalo_oa = request.env['zalo.official.account'].sudo().search(
                [('oa_id', '=', oa_id), ('app_id', '=', app_id)], order='create_date desc', limit=1)
            if not zalo_oa:
                msg = _('Incorrect app id or oa_id')
                return Response.error(msg, code='400').to_json()
            zalo_token = self.get_zalo_token(oa_id, app_id)
            zalo_token_check = request.env['zalo.token']
            if type(zalo_token) != type(zalo_token_check):
                msg = _('Error with token')
                return Response.error(msg, code='400').to_json()
            else:
                # template_id = request.env['zns.template'].sudo().search([('template_id', '=', '219951')], limit=1)
                url = 'https://business.openapi.zalo.me/message/template'
                data = params['data']
                response = requests.post(url, data=json.dumps(data),
                                         headers={'Content-Type': 'application/json',
                                                  'access_token': zalo_token.access_token,
                                                  })
                response = response.json()
                if str(response['error']) == '0':
                    return Response.success('Success', data=response).to_json()
                else:
                    if str(response.get('error')) == '-211':
                        return Response.error(response.get('message'), code='-211').to_json()
                    msg = str(response['error']) + ': ' + response['message']
                    return Response.error(msg, code='400').to_json()
        except Exception as e:
            raise ValidationError(e)

    def get_zalo_token(self, oa_id, app_id):
        zalo_token = request.env['zalo.token'].sudo().search(
            [('oa_id', '=', oa_id), ('app_id', '=', app_id), ('active', '=', True),
             ('expires_access_token', '>', datetime.now())],
            order='create_date desc', limit=1)
        if not zalo_token:
            zalo_token = APIGetToken.get_access_token_by_refresh_token(oa_id, app_id)

        return zalo_token
