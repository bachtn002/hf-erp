# -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_origin = fields.Char('Origin')
    x_preserve = fields.Char('Preserve')
    x_ingredient = fields.Char('Ingredient')
    x_packers = fields.Char('Packers')
    x_supplier_address = fields.Char('Supplier Address')
    x_use_manual = fields.Text('Use Manual')
    x_expiry = fields.Integer('Expiry')
    x_print_stamp = fields.Boolean('Print Stamp')
    x_empty_date = fields.Boolean('Empty date', default= False)
