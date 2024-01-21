# -*- coding: utf-8 -*-

import requests

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.http import request
from odoo.exceptions import ValidationError, UserError
from odoo import _


def get_access_token_by_auth_code(oa_id, auth_code):
    try:
        url = 'https://oauth.zaloapp.com/v4/oa/access_token'
        app_id = request.env['zalo.official.account'].sudo().search([('name', '=', oa_id)])
        code_verifier = request.env['ir.config_parameter'].sudo().get_param('code_verifier')

        data = {
            'code': auth_code,
            'app_id': app_id.app_id,
            'grant_type': 'authorization_code',
            'code_verifier': code_verifier,
        }
        response = requests.post(url, data=data,
                                 headers={'Content-Type': 'application/x-www-form-urlencoded',
                                          'secret_key': app_id.secret_key,
                                          })
        token = response.json()

        if 'expires_in' in token:
            expires_access_token = datetime.now() + timedelta(seconds=float(token['expires_in']))
            expires_refresh_token = datetime.now() + relativedelta(months=3)

            vals = {
                'app_id': app_id.app_id,
                'authorization_code': auth_code,
                'access_token': token['access_token'],
                'refresh_token': token['refresh_token'],
                'expires_access_token': expires_access_token,
                'expires_refresh_token': expires_refresh_token,
                'active': True,
            }
            zalo_token = request.env['zalo.token'].sudo().create(vals)
            return zalo_token
        else:
            raise UserError(_('Message: %s', token['message']))
    except Exception as e:
        raise ValidationError(e)


def get_access_token_by_refresh_token(oa_id, app_id):
    try:
        url = 'https://oauth.zaloapp.com/v4/oa/access_token'
        refresh_token = request.env['zalo.token'].sudo().search(
            [('active', '=', True), ('oa_id', '=', oa_id), ('app_id', '=', app_id),
             ('expires_refresh_token', '>', datetime.now())],
            order='create_date desc', limit=1)

        zalo_oa = request.env['zalo.official.account'].sudo().search(
            [('active', '=', True), ('oa_id', '=', oa_id), ('app_id', '=', app_id)],
            order='create_date desc', limit=1)
        if refresh_token and zalo_oa:
            data = {
                'refresh_token': refresh_token.refresh_token,
                'app_id': app_id,
                'grant_type': 'refresh_token',
            }

            response = requests.post(url, data=data,
                                     headers={'Content-Type': 'application/x-www-form-urlencoded',
                                              'secret_key': zalo_oa.secret_key,
                                              })
            token = response.json()
            if 'access_token' in token:
                expires_access_token = datetime.now() + timedelta(seconds=float(token['expires_in']))
                expires_refresh_token = datetime.now() + relativedelta(months=3)

                refresh_token.access_token = token.get('access_token')
                refresh_token.expires_access_token = expires_access_token
                refresh_token.refresh_token = token.get('refresh_token')
                refresh_token.expires_refresh_token = expires_refresh_token
                return refresh_token
            elif 'error_name' in token:
                zalo_oa.send_message_mail()
                return token['error_name']
        else:
            raise UserError(_('No usable refresh token! You can Callback URL'))
    except Exception as e:
        raise ValidationError(e)


def get_access_token(oa_id, app_id):
    try:
        access_token = request.env['zalo.token'].sudo().search(
            [('oa_id', '=', oa_id), ('app_id', '=', app_id), ('active', '=', True),
             ('expires_access_token', '>=', datetime.now())],
            order='create_date desc', limit=1)

        if not access_token:
            access_token = get_access_token_by_refresh_token(oa_id, app_id)
            access_token_check = request.env['zalo.token']
            if type(access_token) != type(access_token_check):
                return False

        return access_token.access_token
    except Exception as e:
        raise ValidationError(e)
