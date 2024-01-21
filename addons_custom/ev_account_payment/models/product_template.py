# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_reason_in = fields.Boolean(string="Reason In")
    x_can_be_expensed = fields.Boolean(string="Can be expensed")