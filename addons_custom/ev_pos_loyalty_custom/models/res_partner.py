# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_ecommerce = fields.Boolean(string='Is Ecommerce ')
    phone = fields.Char(tracking=True)
    name = fields.Char(index=True, tracking=True)
    ref = fields.Char(string='Reference', index=True, tracking=True)