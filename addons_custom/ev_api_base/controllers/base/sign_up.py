# -*- coding: utf-8 -*-
# Created by hoanglv at 6/1/2020

from odoo.http import route, Controller, request
from odoo import _

from ..helpers import Route, Dispatch, ApiException, Response, middleware

from .sign_in import SignIn


class SignUp(Controller):

    _verify = ['name|str|require',
                'email|str:[\w\.]+@[\w]{2,6}.([a-z]{2,6}){1,3}|require',
                'password|str|require',
                'device_id|str|require',
                'device_info|str',
                'firebase_token|str']

    @route(route=Route('sign_up'), methods=['post'], auth='public', type='json')
    @middleware(auth='none')
    def sign_up(self):
        """
        Đăng ký tại khoản người dùng

        @param params:
            @requires:  name        |   str |   Họ và tên
                        phone       |   str |   Số đt
                        password    |   str |   Mật khẩu
            @options:
        @return:
        """
        email = self.params.get('email', False)
        if not email:
            raise ApiException(_("Error 'email' parameter is missing !"))
        self.params['login'] = email.lower()
        values = {key: self.params.get(key) for key in ('login', 'name', 'password')}

        if self.env["res.users"].sudo().search([("login", "=", self.params.get("login"))]):
            raise ApiException(_('Another user is already registered using this email'), ApiException.AUTHORIZED)

        supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
        lang = request.context.get('lang', '').split('_')[0]
        if lang in supported_lang_codes:
            values['lang'] = lang

        self.env['res.users'].sudo().signup(values, token=None)
        self.env._cr.commit()

        res = Dispatch.dispatch(SignIn(), 'sign_in')
        return Response.success(_('Account registration successful'), data=res).to_json()
