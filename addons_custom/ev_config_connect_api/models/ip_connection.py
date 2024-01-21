# -*- coding: utf-8 -*-
import ipaddress
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class IPConnection(models.Model):
    _name = 'ip.connection'

    name = fields.Char('IP', required=True)
    active = fields.Boolean('Active', default=True)

    _sql_constraints = [
        ('unique_name', 'unique(name)', 'IP must be unique'),
    ]

    @api.onchange('name')
    def is_ipv4(self):
        ip = self.name
        try:
            ipaddress.IPv4Network(ip)
        except:
            raise UserError(_("IP address is invalid! Please check again!"))
