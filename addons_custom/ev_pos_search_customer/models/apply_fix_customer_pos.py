# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosConfigInheritFixCustomer(models.Model):
    _inherit = 'pos.config'

    x_apply_fix_customer = fields.Boolean('Apply fix customer')