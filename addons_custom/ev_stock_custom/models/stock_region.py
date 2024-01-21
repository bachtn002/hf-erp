# -*- coding: utf-8 -*-

from odoo import models, fields

class StockRegion(models.Model):
    _name = 'stock.region'

    code = fields.Char('Code')
    name = fields.Char('Name')

    _sql_constraints = [
        ('code_uniq', 'unique (code)', "The code region already exists in the system.")
    ]
