# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    x_revenue_accounting_by_product = fields.Boolean('Revenue accounting by product')
