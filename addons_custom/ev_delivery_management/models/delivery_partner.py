# -*- coding: utf-8 -*-
from odoo import models, fields


class DeliveryPartner(models.Model):
    _name = 'delivery.partner'
    _description = 'Delivery Partner'
    _order = 'create_date desc'

    code = fields.Char('Code', required=True, index=True)
    name = fields.Char('Name Partner', required=True)
    url = fields.Char('Url', required=True)
    access_token = fields.Char('Access Token', required=True, index=True)
    token_type = fields.Char('Token Type')
    expires_in = fields.Datetime('Expires_in')
    active = fields.Boolean('Active', default=True, index=True)
    internal = fields.Boolean('Internal', default=False, index=True)

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    client_id = fields.Char('Client ID')
    secret_key = fields.Char('Secret Key')
