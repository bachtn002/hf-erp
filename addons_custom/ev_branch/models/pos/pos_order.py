# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError


class pos_order(models.Model):
    _inherit = 'pos.order'

    branch_id = fields.Many2one('res.branch', related='session_id.branch_id')

