# -*- coding: utf-8 -*-
import psycopg2
from odoo import models, fields, api


class ConfigConnection(models.Model):
    _name = 'config.connection'

    name = fields.Char('Host', required=True)
    port = fields.Char('port', required=True)
    user = fields.Char('User', required=True)
    password = fields.Char('Password', required=True)
    database = fields.Char('Database', required=True)
