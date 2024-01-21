# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosConfigInherit(models.Model):
    _inherit = 'pos.config'

    x_number_search_limit = fields.Integer('Number Search Customer Limit')