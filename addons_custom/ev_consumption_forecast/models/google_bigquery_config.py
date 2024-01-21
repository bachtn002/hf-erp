# -*- coding: utf-8 -*-
from odoo import models, fields, api


class GoogleBigqueryConfig(models.Model):
    _name = 'google.bigquery.config'

    name = fields.Char('Name Connection', required=True)
    json_key = fields.Text('Json Key', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (code)', "Name connection already exists on the system!"),
    ]
