# -*- coding: utf-8 -*-
import logging
import requests
import json

from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError

from datetime import datetime
from dateutil.relativedelta import relativedelta


class ZaloOfficialAccountAPI(http.Controller):

    @http.route('/zalo_oa/webhook', methods=['POST'], type='json', auth='public')
    def zalo_oa_webhook(self):
        try:
            data = request.jsonrequest
            event_name = data.get('event_name')
            if event_name == 'user_feedback':
                return {'code': 200}
            app_id = data.get('app_id')
            zalo_id = msg_text = msg_id = tracking_id = ''
            oa_id = data.get('oa_id')
            if data.get('recipient'):
                oa_id = data.get('recipient').get('id')
            if data.get('follower'):
                zalo_id = data.get('follower').get('id')
            if data.get('sender'):
                zalo_id = data.get('sender').get('id')
            if data.get('message'):
                msg_text = data.get('message').get('text')
            if data.get('message'):
                msg_id = data.get('message').get('msg_id')
            if data.get('message'):
                tracking_id = data.get('message').get('tracking_id')
            date = datetime.fromtimestamp(float(data.get('timestamp')) / 1000)
            vals = {
                'data': data,
                'event_name': event_name,
                'app_id': app_id,
                'oa_id': oa_id,
                'zalo_id': zalo_id,
                'msg_text': msg_text,
                'msg_id': msg_id,
                'tracking_id': tracking_id,
                'date': date,
            }
            data_id = request.env['data.webhook.zns'].create(vals)
            data_id.action_confirm()
            return {'code': 200}
        except Exception as e:
            raise ValidationError(e)
