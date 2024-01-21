# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    x_pos_config_old_id = fields.Integer('Pos Config Old Id')