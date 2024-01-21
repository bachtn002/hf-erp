# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, SUPERUSER_ID


class ProductTemplate(models.Model):
    _inherit = "product.template"

    name = fields.Char(translate=False)
