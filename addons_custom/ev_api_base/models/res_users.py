# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.addons.http_routing.models.ir_http import slugify_one

from ..helpers.Html import Html

import jwt
import requests



class ResUsers(models.Model):
    _inherit = 'res.users'

    device_ids = fields.One2many('res.users.device', 'user_id', string='Access device')

    def get_image_user(self, width_x_height='512x512'):
        return '{0}user/image/{1}/{2}/{3}.png'.format(Html().URL_ROOT, self.partner_id.id, width_x_height,
                                                      slugify_one(self.name))

    def is_access_token_expired(self, access_token):
        # Nếu quá hạn trả về True
        sign = access_token.split('.')[2]
        for device in self.device_ids:
            if device.access_token == sign and (not device.expired or device.expired < datetime.now()):
                device.unlink()
                return True
        return False

    def reset_access_token_expire(self, access_token):
        expire = self.get_expired()
        sign = access_token.split('.')[2]
        for device in self.device_ids:
            if device.access_token == sign and device.expired <= (datetime.now() + relativedelta(days=3)):
                device.expired = expire
                break

    def get_expired(self):
        return datetime.now() + relativedelta(
            seconds=int(self.env.ref('ec_api_base.access_token_expired').sudo().value))

    def reset_password(self, login):
        """ retrieve the user corresponding to login (login or email),
            and reset their password
        """
        users = self.search([('login', '=', login)])
        if not users:
            users = self.search([('email', '=', login)])
        if len(users) == 1 and users.oauth_provider_id:
            raise Exception(_('Reset password error: This email was registered through the social network account.'))
        res = super(ResUsers, self).reset_password(login)
        return res
