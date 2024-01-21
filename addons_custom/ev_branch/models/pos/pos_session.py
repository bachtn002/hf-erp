# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class pos_session(models.Model):
    _inherit = 'pos.session'

    branch_id = fields.Many2one('res.branch', related='config_id.branch_id')

