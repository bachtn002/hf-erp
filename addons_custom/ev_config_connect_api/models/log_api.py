# -*- coding: utf-8 -*-
import psycopg2
from odoo import models, fields, api


class LogAPI(models.Model):
    _name = 'log.api'
    _rec_name = 'code_api'

    code_api = fields.Char('Code API')
    name_api = fields.Char('Name API')
    params = fields.Text('Params')
    code_response = fields.Char(string='Response')
    mess_response = fields.Text(string='Response Messege')
    remote_ip = fields.Text(string='Remote IP address')
