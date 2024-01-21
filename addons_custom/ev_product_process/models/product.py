# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError, except_orm
from odoo.osv import osv


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_property_stock_manufactory_id = fields.Many2one(
        'stock.location', "Inventory Process Location",
        company_dependent=True, check_company=True,
        domain="[('usage', '=', 'inventory'), '|', ('company_id', '=', False), ('company_id', '=', allowed_company_ids[0])]")
