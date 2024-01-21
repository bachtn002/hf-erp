# -*- coding: utf-8 -*-
# Created by hoanglv at 6/1/2020

from odoo.http import route, Controller
from odoo import _

from ..helpers import Route, Response, Authentication, middleware


class SignIn(Controller):

    _verify = ['login|str|require',
                'password|str|require:type{"odoo"}',
                'idToken|str|require:type{"facebook","google"}',
                'image|str|require:type{"facebook","google"}',
                'device_id|str|require',
                'type|str|require',
                'device_info|str',
                'firebase_token|str']

    @route(route=Route('sign_in'), methods=['post'], auth='public', type='json')
    @middleware()
    def sign_in(self):
        """
        Đăng nhập hệ thống

        @param params: Danh sách tham số gửi lên từ client
            @requires:  login           | str   |   email
                        password        | str   |   mật khẩu
                        device_id       | str   |   id thiết bị đăng nhập
                        idToken         | str   |   id token khi đăng nhập Social Network
                        image           | str   |   ảnh đại diện người dùng
            @options:   device_info     | str   |   Thông tin thiết bị đăng nhập
                        firebase_token  | str   |   Firebase tooken
        @return: Trả về thông tin user đăng nhập
        """
        device_id = (self.params['device_id']).strip()
        image = self.params.get('image')
        login = self.params['login'].lower()
        user = self.env['res.users'].search([('login', '=', login)])

        self._clear_duplicate_device(user)
        access_token = Authentication.generate_access_token(login, self.params['device_id'])
        header, payload, sign = access_token.split('.')
        UserDevice = self.env['res.users.device']

        device = self.env['res.users.device'].search([('user_id', '=', user.id), 
                                                      ('device_id', '=', self.params['device_id'])])
        if device:
            device.write({'firebase_token': self.params.get('firebase_token', ''), 
                          'access_token': sign})
        else:
            UserDevice.create({'user_id': user.id,
                               'device_id': self.params.get('device_id'),
                               'device_info': self.params.get('device_info', ''),
                               'access_token': sign,
                               'firebase_token': self.params.get('firebase_token', '')})

        user._update_last_login()
        user.reset_access_token_expire(access_token)

        data = {}
        if self.params.get('user_type', False) == 'portal':
            data = self.__get_portal_user_data(user, access_token, image)
        elif self.params.get('user_type', False) == 'internal':
            data = self.__get_internal_user_data(user, access_token)

        return Response.success('', data=data).to_json()

    def _clear_duplicate_device(self, user):
        devices = self.env['res.users.device'].sudo().search([('user_id', '=', user.id),
                                                              ('device_id', '=', self.params['device_id'])], 
                                                              order='expired DESC')
        device = False
        if len(devices) <= 1:
            return
        device_len = len(devices)
        while device_len > 1:
            device_len-=1
            devices[device_len].unlink()

    def __get_portal_user_data(self, user, access_token, image):
        url = user.get_image_user()
        if image:
            url = image
        support_user_inf = {
            'id': None,
            'name': '',
            'image': '',
            'phone': ''
        }
        have_support_user = False
        if user.partner_id.user_id:
            have_support_user = True
            support_user = user.partner_id.user_id.sudo()
            support_user_inf.update({
                'id': support_user.id,
                'name': support_user.name or '',
                'image': support_user.get_image_user(),
                'phone': support_user.partner_id.phone or ''
            })
        data = {
            'user_type': 'portal',
            'access_token': access_token,
            'user_id': {'id': user.id,
                        'name': user.name or '',
                        'login': user.login or '',
                        'phone': user.partner_id.phone or '',
                        'image': url},
            'support_user_id': support_user_inf,
            'have_support_user': have_support_user,
            'company_id': {'id': user.company_id.id,
                           'name': user.company_id.name or ''}
        }
        return data

    def __get_internal_user_data(self, user, access_token):
        url = user.get_image_user()
        roles = Authentication.get_user_roles(user)

        data = {
            'user_type': 'internal',
            'access_token': access_token,
            'user_id': {'id': user.id,
                        'name': user.name or '',
                        'login': user.login or '',
                        'phone': user.partner_id.phone or '',
                        'image': url},
            'partner_id': {'id': user.partner_id.id,
                           'name': user.partner_id.name or ''},
            'company_id': {'id': user.company_id.id,
                           'name': user.company_id.name or ''},
            'roles': roles
        }
        return data
