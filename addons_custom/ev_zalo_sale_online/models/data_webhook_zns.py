# -*- coding: utf-8 -*-

from odoo import models, fields, _
import json

import requests
from ...ev_zalo_notification_service.helpers import APIGetToken

URL = "https://openapi.zalo.me/v3.0/oa/message/cs"


class DataWebhookZNS(models.Model):
    _inherit = 'data.webhook.zns'

    def send_message_notify_delivery(self, zalo_id, oa_id, app_id, name_partner,
                                     order_code, minutes, track_url):
        try:
            headers = {
                'access_token': APIGetToken.get_access_token(
                    oa_id, app_id),
                'Content-Type': 'application/json'
            }
            if track_url:
                data = {
                    "recipient": {
                        "user_id": zalo_id
                    },
                    "message": {
                        "text": name_partner + " ơi! Đơn hàng " + order_code + " đang trên đường giao dự kiến trong " + str(
                            minutes) + " phút tới. Thời gian vận chuyển có thể lâu hơn do tắc đường, mong Quý khách thông cảm. "
                                       "Quý khách vui lòng chú ý điện thoại, tài xế sẽ liên hệ để giao hàng nhé!",
                        "attachment": {
                            "type": "template",
                            "payload": {
                                "buttons": [
                                    {
                                        "title": "Theo dõi đơn vận chuyển",
                                        "payload": {
                                            "url": track_url
                                        },
                                        "type": "oa.open.url"
                                    }
                                ]
                            }
                        }
                    }
                }
            else:
                data = {
                    "recipient": {
                        "user_id": zalo_id
                    },
                    "message": {
                        "text": name_partner + " ơi! Đơn hàng " + order_code + " đang trên đường giao dự kiến trong " + str(
                            minutes) + " phút tới. Thời gian vận chuyển có thể lâu hơn do tắc đường, mong Quý khách thông cảm. "
                                       "Quý khách vui lòng chú ý điện thoại, tài xế sẽ liên hệ để giao hàng nhé!",
                    }
                }
            response = requests.post(URL, data=json.dumps(data),
                                     headers=headers,
                                     verify=False)
            response = response.json()
            message = response.get('message')
            return message
        except Exception as error:
            return error
