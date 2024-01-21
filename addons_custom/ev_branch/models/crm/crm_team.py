# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm
import re

class CrmTeam(models.Model):
    _inherit = 'crm.team'

    def _default_branch_id(self):
        branch_id = self.env['res.users'].browse(self._uid).branch_id.id
        return branch_id

    branch_id = fields.Many2one('res.branch', default=_default_branch_id)
