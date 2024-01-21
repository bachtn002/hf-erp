# -*- coding: utf-8 -*-

from odoo import models, fields, _


class OTPZalo(models.Model):
    _name = 'otp.zalo'
    _description = 'OTP Zalo user send to confirm'
    _order = 'create_date desc'

    name = fields.Char('OTP', required=True)
    user_id = fields.Char('User Zalo ID', required=True)
    phone = fields.Char('Phone', required=True)
    expired = fields.Datetime('Expired OTP', required=True)
    active = fields.Boolean('Active', default=True)


