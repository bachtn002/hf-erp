# -*- coding: utf-8 -*-
from odoo import _, models, api, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    x_show_product_list = fields.Boolean('Show list Product Screen', copy=True)
