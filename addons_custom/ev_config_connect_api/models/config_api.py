# -*- coding: utf-8 -*-
import psycopg2
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ConfigAPI(models.Model):
    _name = 'config.api'

    code = fields.Char('Code API', required=True)
    name = fields.Char('Name API', required=True)
    token = fields.Char('Token', required=True)
    active = fields.Boolean(string='Active', default=True)

    connection_id = fields.Many2one('config.connection', string='Connection')

    preventive = fields.Boolean(string='Preventive', default=False)
    connection_preventive = fields.Many2one('config.connection', string='Connection Preventive')

    _sql_constraints = [
        ('code_uniq', 'unique (code)', "Code api already exists on the system!"),
        ('token_uniq', 'unique (token)', "Token api already exists on the system!"),
    ]

    @api.onchange('connection_id')
    def _onchange_connection_id(self):
        try:
            if self.connection_id:
                return {'domain': {'connection_preventive': [('id', '!=', self.connection_id.id)]}}
            else:
                return {'domain': {'connection_preventive': [(1, '=', 1)]}}
        except Exception as e:
            raise ValidationError(e)
