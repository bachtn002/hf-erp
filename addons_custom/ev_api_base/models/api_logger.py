# -*- coding: utf-8 -*-
# Created by hoanglv at 6/4/2020

from odoo import api, fields, models


class ApiLogger(models.Model):
    _name = 'api.logger'
    _description = 'Api logger'
    _order = 'create_date DESC'

    user_id = fields.Many2one('res.users', string='Action User')
    name = fields.Char(string='API')
    params = fields.Text(string='Params')
    exception = fields.Char(string='Exception')
    exception_message = fields.Char(string='Exception message')
    exception_data = fields.Text(string='Exception data')
