# -*- coding: utf-8 -*-

from odoo import _, models, api, fields


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    is_rank_discount = fields.Boolean(default=False, string='Is rank discount')


