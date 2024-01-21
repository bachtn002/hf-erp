# -*- coding: utf-8 -*-

from odoo import models, fields, api

from datetime import datetime
from dateutil.relativedelta import relativedelta


class ResUsersDevice(models.Model):
    _name = 'res.users.device'
    _description = 'User access device'

    device_id = fields.Char(string="Device")
    device_info = fields.Text(string="Device info")
    access_token = fields.Char(string='Access token')
    expired = fields.Datetime(string="Expired", required=True)
    firebase_token = fields.Char(string="Firebase Token")
    user_id = fields.Many2one('res.users', "User")

    @api.model
    def create(self, vals):
        if 'expired' not in vals:
            vals.update({'expired': self.get_expired()})

        return super(ResUsersDevice, self).create(vals)

    def get_expired(self):
        return datetime.now() + relativedelta(seconds=int(self.env.ref('ec_api_base.access_token_expired').sudo().value))