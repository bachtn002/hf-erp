# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class Product(models.Model):
    _inherit = 'product.template'

    is_package_cover = fields.Boolean(string='Is package cover')