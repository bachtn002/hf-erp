# -*- coding: utf-8 -*-

import ipaddress
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class IPSendZNS(models.Model):
    _name = 'ip.send.zns'
    _description = 'IP Send ZNS'
    _order = 'create_date desc'

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

    def action_read_ip(self):
        self.ensure_one()
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ip.send.zns',
            'res_id': self.id,
        }
