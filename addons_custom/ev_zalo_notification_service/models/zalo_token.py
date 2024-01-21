# -*- coding: utf-8 -*-

import requests
import json

from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError

from datetime import datetime


class ZaloToken(models.Model):
    _name = 'zalo.token'
    _description = 'Zalo Token Management'
    _order = 'create_date desc'

    app_id = fields.Char('App ID', required=True)
    # oa_id = fields.Char('OA ID', required=True)
    access_token = fields.Char('Access Token', required=True)
    refresh_token = fields.Char('Refresh Token', required=True)
    expires_access_token = fields.Datetime('Expire Access Token', required=True)
    expires_refresh_token = fields.Datetime('Expire Refresh Token', required=True)
    authorization_code = fields.Char('Authentication Code')
    active = fields.Boolean('Active', default=True)

    def get_access_token(self):
        try:
            if not self.active:
                return
            if self.expires_access_token > datetime.now():
                return
            if not self.refresh_token or self.expires_refresh_token <= datetime.now():
                return

            base_url = self.env['ir.config_parameter'].sudo().get_param('url_api_zalo')
            url = base_url + '/zalo_oa/access_token'
            data = {
                'oa_id': self.oa_id,
                'app_id': self.app_id,
            }
            response = requests.post(url, data=json.dumps(data),
                                     headers={'Content-Type': 'application/json'},
                                     verify=False)
            response = response.json()
            if response.get('result').get('code') == '400':
                raise UserError(_(response['result']['message']))
            if response.get('result').get('code') == 200:
                self.access_token = response.get('result').get('data').get('access_token')
                self.expires_access_token = response.get('result').get('data').get('expires_access_token')
                self.refresh_token = response.get('result').get('data').get('refresh_token')
                self.expires_refresh_token = response.get('result').get('data').get('expires_refresh_token')
            else:
                self.active = False

        except Exception as e:
            raise ValidationError(e)
