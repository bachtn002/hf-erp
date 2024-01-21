# -*- coding: utf-8 -*-
import json
import ast
import random
import string
import requests
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from datetime import datetime, timedelta
from ..helpers import APIGetToken, APIZNS

_logger = logging.getLogger(__name__)


class DataWebhookZNS(models.Model):
    _name = 'data.webhook.zns'
    _description = 'Data Webhook ZNS'
    _order = 'create_date desc'

    data = fields.Text('Data')
    message = fields.Text('Message')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('queue', 'Queue'),
        ('done', 'Done')],
        'State', default='draft')

    def action_confirm(self):
        try:
            self.state = 'queue'
            # self._action_done()
            self.sudo().with_delay(channel='root.action_confirm_webhook', max_retries=3)._action_done()
        except Exception as e:
            raise ValidationError(e)

    def _action_done(self):
        try:

            data = ast.literal_eval(self.data)
            event_name = data.get('event_name') if 'event_name' in data else ''
            sender = data.get('sender').get('id') if 'sender' in data else ''
            # follower = data.get('follower')['id'] if 'follower' in data else ''
            # partner_id = self.check_partner(follower)
            # if event_name == 'follow' and partner_id:
            #     partner_id.x_zalo_follow = True
            # if event_name == 'unfollow' and partner_id:
            #     partner_id.x_zalo_follow = False

            if event_name == 'user_send_text':
                text = data.get('message').get('text')
                msg_id = data.get('message').get('msg_id')
                self.action_parsing(sender, msg_id, text)
            # Không dùng map partner từ tin zns xác nhận đơn hàng do Zalo k còn trả về zalo_id
            # elif event_name == 'user_received_message':
            #     self.action_user_received_message()
            elif event_name == 'follow':
                self.action_map_partner_by_follow()
            self.state = 'done'
        except Exception as e:
            raise ValidationError(e)

    def check_partner(self, user_id):
        try:
            zalo_id = self.env['res.partner.zalo'].sudo().search([('zalo_id', '=', user_id)], limit=1)
            if zalo_id:
                return zalo_id
            else:
                return False
        except Exception as e:
            raise ValidationError(e)

    def action_parsing(self, sender, msg_id, text):
        try:
            syntax = text.split(' ')[0]
            value = text.split(' ')[1] if len(text.split(' ')) > 1 else ''
            syntax_map_partner = self.env['ir.config_parameter'].sudo().get_param('syntax_map_partner')
            syntax_search_point = self.env['ir.config_parameter'].sudo().get_param('syntax_search_point')
            syntax_otp = self.env['ir.config_parameter'].sudo().get_param('syntax_otp_map')

            if syntax == syntax_map_partner:
                self.action_send_otp(sender, msg_id, value)
            elif syntax == syntax_search_point:
                self.action_search_point(sender, msg_id)
            elif syntax == syntax_otp:
                self.action_map_partner(sender, msg_id, value)
            else:
                msg = _('Lỗi cú pháp. Bạn vui lòng kiểm tra lại cú pháp!')
                self.send_feedback_message(sender, msg_id, msg)
                return
        except Exception as e:
            raise ValidationError(e)

    def action_send_otp(self, sender, msg_id, phone):
        try:
            zalo_id = self.env['res.partner.zalo'].sudo().search([('phone', '=', phone), ('zalo_id', '=', sender)],
                                                                 limit=1)
            if zalo_id:
                msg = _('Số điện thoại đã được đăng ký trên hệ thống.')
                self.send_feedback_message(sender, msg_id, msg)
                return
            code = ''.join(random.choices(string.digits, k=4))
            expired = datetime.now() + timedelta(minutes=5)
            vals = {
                'name': code,
                'user_id': sender,
                'phone': phone,
                'expired': expired,
                'active': True,
            }
            otp_zalo = self.env['otp.zalo'].create(vals)
            data = ast.literal_eval(self.data)
            app_id = data.get('app_id')
            oa_id = data.get('recipient').get('id')
            send_otp = APIZNS.send_zns_otp(app_id, oa_id, otp_zalo.name, otp_zalo.phone)
            if send_otp and type(send_otp) == bool:
                msg = _('Hệ thống đã gửi cho bạn số OTP để xác thực số điện thoại.\n'
                        'Hãy soạn tin và gửi lại theo cú pháp: #otp + khoảng trắng + số OTP.')
                self.send_feedback_message(sender, msg_id, msg)
                return
            elif not send_otp and type(send_otp) == bool:
                msg = _('Hệ thống không gửi được OTP qua Zalo theo số điện thoại của bạn. Vui lòng kiểm tra lại.')
                self.send_feedback_message(sender, msg_id, msg)
                return
            else:
                msg = _('Hệ thống hiện tại không gửi được OTP qua Zalo. Vui lòng thực hiện vào ngày sau.')
                self.send_feedback_message(sender, msg_id, msg)
                self.message = send_otp
                return

        except Exception as e:
            raise ValidationError(e)

    def action_search_point(self, sender, msg_id):
        try:
            data_webhook = ast.literal_eval(self.data)
            app_id = data_webhook.get('app_id')
            oa_id = data_webhook.get('recipient').get('id')
            check_follow = APIZNS.get_profile(sender, app_id, oa_id)
            if not check_follow:
                msg = _('Bạn hãy quan tâm Zalo Homefarm để thực hiện chức năng này')
                self.send_feedback_message_follow(sender, msg_id, msg)
                return

            zalo_id = self.check_partner(sender)
            if not zalo_id:
                msg = _('Bạn cần đăng ký liên kết tài khoản để thực hiện chức năng này.\n'
                        'Để đăng ký tài khoản, vui lòng soạn tin và gửi theo cú pháp: #dk + khoảng trắng + số điện thoại.\n'
                        'Ví dụ: #dk 0900000001')
                self.send_feedback_message(sender, msg_id, msg)
                return

            partner_id = self.env['res.partner'].sudo().search([('phone', '=', zalo_id.phone)], limit=1)
            points = '{:,.0f}'.format(partner_id.loyalty_points) if partner_id else 0
            msg = _('Điểm tích lũy của bạn là %s điểm', points)
            self.send_feedback_message(sender, msg_id, msg)
            return
        except Exception as e:
            raise ValidationError(e)

    def action_map_partner(self, sender, msg_id, otp):
        try:
            data_webhook = ast.literal_eval(self.data)
            oa_id = data_webhook.get('recipient').get('id')
            app_id = data_webhook.get('app_id')
            expired = datetime.now()
            otp_zalo = self.env['otp.zalo'].search([('name', '=', otp), ('user_id', '=', sender)], limit=1)

            if not otp_zalo:
                msg = _('Mã OTP không đúng, vui lòng kiểm tra lại!')
                self.send_feedback_message(sender, msg_id, msg)
                return
            else:
                if otp_zalo.expired < expired:
                    msg = _('Mã OTP đã hết hạn sử dụng. Bạn phải thực hiện lại.')
                    self.send_feedback_message(sender, msg_id, msg)
                    return

            zalo_id = self.env['res.partner.zalo'].sudo().search([('zalo_id', '=', sender)], limit=1)
            if zalo_id:
                zalo_id.phone = otp_zalo.phone
            else:
                date = datetime.now()
                query = """
                    INSERT INTO res_partner_zalo (zalo_id, phone, oa_id, app_id, create_uid, create_date, write_uid, write_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """
                self.env.cr.execute(query,
                                    (sender, otp_zalo.phone, oa_id, app_id, self.create_uid.id, date, self.write_uid.id, date))
            msg = _('Chúc mừng bạn đã đăng ký liên kết tài khoản thành công')
            self.send_feedback_message(sender, msg_id, msg)
            return
        except Exception as e:
            raise ValidationError(e)

    def get_zns_by_message(self, msg_id):
        query = """
            SELECT *
            from zns_information
            where msg_id = '%s'
            limit 1;
        """
        self.env.cr.execute(query % (msg_id))
        values = self.env.cr.dictfetchall()
        if len(values) > 0:
            return values
        return False

    def _get_zalo_list_recent_chats(self, user_id):
        max_times_call_api = 10
        offset = 0
        # Max 10 message per request.
        count = 10
        while (max_times_call_api > 0):
            try:
                base_url = 'https://openapi.zalo.me/v2.0/oa/conversation'
                url = base_url + '?data={"user_id":\"%s\","offset":\"%s\","count":\"%s\"}' % (user_id, offset, count)

                data_webhook = ast.literal_eval(self.data)
                app_id = data_webhook.get('app_id')
                oa_id = data_webhook.get('oa_id')
                access_token = APIGetToken.get_access_token(oa_id, app_id)
                response = requests.get(url, headers={'access_token': access_token}, verify=False)
                if response.status_code == 200:
                    data = response.json()
                    # Case call api success and no exception
                    if data.get('error') == 0:
                        # Case out of offset => response success but data []
                        if len(data.get('data')) > 0:
                            for msg in data.get('data'):
                                if msg['type'] == 'nosupport':
                                    zns_sent = self.get_zns_by_message(msg['message_id'])
                                    if zns_sent:
                                        return zns_sent
                        else:
                            break
                    else:
                        raise ValidationError(data.get('message'))
                offset += 11
                max_times_call_api -= 1
            except Exception as e:
                raise ValidationError(e)

    def action_map_partner_by_follow(self):
        try:
            zalo_id = self.env['res.partner.zalo'].sudo().search([('zalo_id', '=', self.zalo_id)], limit=1)
            if zalo_id:
                return
            # call api Lấy danh sách các hội thoại với người dùng
            zns_sent = self._get_zalo_list_recent_chats(self.zalo_id)

            if zns_sent:
                customer_phone = zns_sent[0].get('phone')
                # OA va APP id Homefarm
                data_zns = ast.literal_eval(zns_sent[0].get('data'))
                oa_id = data_zns.get('oa_id')
                app_id = data_zns.get('app_id')

                date = datetime.now()
                query = """
                        INSERT INTO res_partner_zalo (zalo_id, phone, oa_id, app_id, create_uid, create_date, write_uid, write_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                    """
                self.env.cr.execute(query, (self.zalo_id, customer_phone, oa_id, app_id, self.create_uid.id, date, self.write_uid.id, date))
        except Exception as e:
            raise ValidationError(e)

    def send_feedback_message(self, user_id, msg_id, message):
        try:
            url = 'https://openapi.zalo.me/v3.0/oa/message/cs'
            data = {
                'recipient': {
                    # 'message_id': msg_id
                    'user_id': user_id
                },
                'message': {
                    'text': message

                }
            }
            data_webhook = ast.literal_eval(self.data)
            app_id = data_webhook.get('app_id')
            oa_id = data_webhook.get('recipient').get('id')
            access_token = APIGetToken.get_access_token(oa_id, app_id)
            response = requests.post(url, data=json.dumps(data),
                                     headers={'Content-Type': 'application/json',
                                              'access_token': access_token,
                                              })
            if response.status_code == 200:
                response = response.json()
                self.state = 'done'
                self.message = response.get('message')
        except Exception as e:
            raise ValidationError(e)

    def send_feedback_message_follow(self, user_id, msg_id, message):
        try:
            url = 'https://openapi.zalo.me/v3.0/oa/message/cs'
            data = {
                'recipient': {
                    # 'message_id': msg_id
                    'user_id': user_id
                },
                'message': {
                    'text': message,
                    'attachment': {
                        'type': 'template',
                        'payload': {
                            'template_type': 'media',
                            'elements': [
                                {
                                    'media_type': 'image',
                                    'attachment_id': 'RL6LDPTZXqvkLvCsd6ITN6v5XIMRTfD1UKQJCu1rWLTYGe4bW2dN6J1PptxVE9zLVaZ9CDCuZ5LZKy5fp7wPG6WJbNx6Fu86C0-MUiCwZ0Ss0PXzpZQ91ZeQoIZA8DvLF1h9VyvuYGKvJyuloYx23NfAmZZ00o98rd26Nm'
                                }
                            ]
                        }
                    }
                },

            }
            data_webhook = ast.literal_eval(self.data)
            app_id = data_webhook.get('app_id')
            oa_id = data_webhook.get('recipient').get('id')
            access_token = APIGetToken.get_access_token(oa_id, app_id)
            response = requests.post(url, data=json.dumps(data),
                                     headers={'Content-Type': 'application/json',
                                              'access_token': access_token,
                                              })
            if response.status_code == 200:
                response = response.json()
                self.state = 'done'
                self.message = response.get('message')
        except Exception as e:
            raise ValidationError(e)

    def send_message_attachment(self, user_id, msg_id, msg_text, title, link):
        # Zalo ver 3 k support dạng gửi attachment button
        try:
            url = 'https://openapi.zalo.me/v3.0/oa/message/cs'
            data = {
                'recipient': {
                    # 'message_id': msg_id
                    'user_id': user_id
                },
                "message": {
                    "text": msg_text,
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "buttons": [
                                {
                                    "title": title,
                                    "payload": {
                                        "url": link
                                    },
                                    "type": "oa.open.url"
                                },
                            ]
                        }
                    }
                }
            }
            data_webhook = ast.literal_eval(self.data)
            app_id = data_webhook.get('app_id')
            oa_id = data_webhook.get('recipient').get('id')
            access_token = APIGetToken.get_access_token(oa_id, app_id)
            response = requests.post(url, data=json.dumps(data),
                                     headers={'Content-Type': 'application/json',
                                              'access_token': access_token,
                                              })
            if response.status_code == 200:
                response = response.json()
                self.state = 'done'
                self.message = response.get('message')
        except Exception as e:
            raise ValidationError(e)


    def action_delete_data(self):
        try:
            query = """
                DELETE FROM data_webhook_zns where state = 'done'; 
            """
            self.env.cr.execute(query)
            self.env.cr.commit()
            # vacuum = 'VACUUM FULL'
            # self.env.cr.execute(vacuum)
        except Exception as e:
            raise ValidationError(e)

    def action_user_received_message(self):
        try:
            # webhook trả sự kiện người dùng nhận tin nhắn zns. Nếu là zns đơn hàng thì map partner với oa
            data_webhook = ast.literal_eval(self.data)
            oa_id = data_webhook.get('sender').get('id')
            app_id = data_webhook.get('app_id')
            sender = data_webhook.get('recipient').get('id')
            tracking_id = data_webhook.get('message').get('tracking_id')

            zns_id = self.env['zns.information'].sudo().search([('tracking_id', '=', tracking_id)], limit=1)
            if not zns_id:
                return

            zalo_id = self.env['res.partner.zalo'].sudo().search([('zalo_id', '=', sender)], limit=1)

            if zalo_id:
                zalo_id.phone = zns_id.phone
            else:
                date = datetime.now()
                query = """
                    INSERT INTO res_partner_zalo (zalo_id, phone, oa_id, app_id, create_uid, create_date, write_uid, write_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """
                self.env.cr.execute(query,
                                    (sender, zns_id.phone, oa_id, app_id, self.create_uid.id, date, self.write_uid.id, date))
            return
        except Exception as e:
            raise ValidationError(e)
