# -*- coding: utf-8 -*-
import requests

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError


class RateZNS(models.Model):
    _name = 'rate.zns'
    _description = 'Customer rating zns management'
    _order = 'submit_date desc'

    template_id = fields.Char('Template ID', index=True)
    note = fields.Text('Note')
    rate = fields.Integer('Rate', default=0, index=True)
    submit_date = fields.Datetime('Submit Date', index=True)
    msg_id = fields.Char('Message ID', index=True)
    feed_back = fields.Text('Feedback')
    tracking_id = fields.Char('Tracking ID', index=True)
    oa_id = fields.Char('OA ID')

    def _get_rate_zns(self):
        try:
            url = 'https://business.openapi.zalo.me/rating/get'
            template_ids = self.env['zns.template'].sudo().search(
                [('template_tag', '=', 'post_transaction'), ('status', '=', 'enable')])

            from_time = int(datetime.now().replace(hour=00, minute=00, second=00).timestamp() * 1000)
            to_time = int(datetime.now().replace(hour=23, minute=59, second=59).timestamp() * 1000)

            for template_id in template_ids:
                zalo_oa = self.env['zalo.official.account'].sudo().search(
                    [('oa_id', '=', template_id.oa_id), ('app_id', '=', template_id.app_id)])
                if not zalo_oa:
                    continue

                token = self.get_access_token(template_id.oa_id, template_id.app_id)

                params = {
                    'template_id': template_id.template_id,
                    'from_time': from_time,
                    'to_time': to_time,
                    'offset': 0,
                    'limit': 10000
                }

                response = requests.get(url=url, params=params, headers={'Content-Type': 'application/json',
                                                                         'access_token': token})
                if response.status_code == 200:
                    response = response.json()
                    if response.get('error') != 0:
                        continue
                    if len(response.get('data').get('data')) <= 0:
                        continue
                    for dt in response.get('data').get('data'):
                        msg_id = dt.get('msgId')
                        tracking_id = dt.get('trackingId')
                        oa_id = dt.get('oaId')
                        ms = float(dt.get('submitDate'))
                        submit_date = datetime.fromtimestamp(ms / 1000.0)
                        # Sangnt comment: 1 tracking_id (Đơn hàng) cho phép gửi đánh giá nhiều lần
                        rate_zns = self.env['rate.zns'].search([('msg_id', '=', msg_id), ('submit_date', '=', submit_date)])
                        if rate_zns:
                            continue
                        vals = {
                            'template_id': template_id.template_id,
                            'note': dt.get('note'),
                            'rate': dt.get('rate'),
                            'msg_id': msg_id,
                            'feed_back': dt.get('feedbacks'),
                            'tracking_id': tracking_id,
                            'submit_date': submit_date,
                            'oa_id': oa_id,
                        }
                        self.env['rate.zns'].create(vals)

        except Exception as e:
            raise ValidationError(e)

    def get_access_token(self, oa_id, app_id):
        try:
            access_token = self.env['zalo.token'].sudo().search(
                [('oa_id', '=', oa_id), ('app_id', '=', app_id), ('active', '=', True),
                 ('expires_access_token', '>=', datetime.now())],
                order='create_date desc', limit=1)

            if not access_token:
                access_token = self.get_access_token_by_refresh_token(oa_id, app_id)
                access_token_check = self.env['zalo.token']
                if type(access_token) != type(access_token_check):
                    return False

            return access_token.access_token
        except Exception as e:
            raise ValidationError(e)

    def get_access_token_by_refresh_token(self, oa_id, app_id):
        try:
            url = 'https://oauth.zaloapp.com/v4/oa/access_token'
            refresh_token = self.env['zalo.token'].sudo().search(
                [('active', '=', True), ('oa_id', '=', oa_id), ('app_id', '=', app_id),
                 ('expires_refresh_token', '>', datetime.now())],
                order='create_date desc', limit=1)

            zalo_oa = self.env['zalo.official.account'].sudo().search(
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
