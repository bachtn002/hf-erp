# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class SourceOrder(models.Model):
    _name = 'source.order'
    _description = 'Source Order'
    _order = 'code asc'

    name = fields.Char('Source Order', required=True)
    code = fields.Char('Code', required=True)
    active = fields.Boolean(default=True)

    sql_constraints = [
        ('name_uniq', 'unique (name)', 'The Source Order already exists in the system!'),
        ('code_uniq', 'unique (code)', 'The Source Order Code already exists in the system!')
    ]
