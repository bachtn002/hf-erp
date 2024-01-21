# -*- coding: utf-8 -*-

from odoo import models, fields


class ZaloOfficialAccount(models.Model):
    _inherit = 'zalo.official.account'

    name = fields.Char('Name OA', required=True)
    oa_id = fields.Char('OA ID', required=True)
    template_otp = fields.Char('Template OTP')
