# -*- coding: utf-8 -*-
# Created by HieuDo at 15/9/2020

from odoo.http import route, Controller
from odoo import _

from ..helpers import Route, Dispatch, ApiException, Response, middleware


class ForgotPassword(Controller):

    _verify = ['email|str|require']

    @route(route=Route('forgot_password'), methods=['post'], auth='public', type='json')
    @middleware(auth='user')
    def forgot_password(self):
        """
        Quên mật khẩu

        @param params: Danh sách tham số gửi lên từ client
            @requires:  email           | str   |   email
        @return: Trả về message thông báo
        """
        login = self.params['email']
        data = {}
        try:
            assert login, _("No login provided.")
            self.env['res.users'].sudo().reset_password(login)
            return Response.success(_("An email has been sent with credentials to reset your password"), data=[]).to_json()
        except UserError as e:
            return Response.error(e.name or e.value, data={}).to_json()
        except SignupError:
            return Response.error(_("Could not reset your password"), data={}).to_json()
        except Exception as e:
            return Response.error(str(e), data={}).to_json()
