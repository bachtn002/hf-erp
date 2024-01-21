# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'

    is_stage_back = fields.Boolean(string='Is stage back', default=False)
