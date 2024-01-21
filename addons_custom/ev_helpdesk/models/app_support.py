# -*- coding: utf-8 -*-

from odoo import models, fields


class AppSupport(models.Model):
    _name = 'app.support'
    _description = 'Means of Support'
    _order = 'create_date desc'

    name = fields.Char('App Support', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The app support already exists in the system!')
    ]
