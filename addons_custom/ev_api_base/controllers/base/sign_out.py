# -*- coding: utf-8 -*-
# Created by hoanglv at 6/1/2020

from odoo.http import route, Controller
from odoo import _

from ..helpers import Route, Dispatch, Response, ApiException, LOGGER, middleware


class SignOut(Controller):

    @route(route=Route('sign_out'), methods=['post'], auth='public', type='json')
    @middleware(auth='user')
    def sign_out(self):

        """
        Đăng xuất

        @param params: Danh sách tham số gửi lên từ client
            @requires:  access_token    | str   | Access token
            @options:
        @return: Trả về true nếu đăng nhập thành công
                        message nếu đăng nhập thất bại
        """
        header, payload, sign = self.params.get('access_token').split('.')

        UserDevice = self.env['res.users.device']

        check_exist_login = UserDevice.search([('access_token', '=', sign)])
        if check_exist_login:
            check_exist_login.unlink()
        
        return Response.success(_('Logged out successfully!'), {}).to_json()
