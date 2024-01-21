# -*- coding: utf-8 -*-

from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    x_user_id = fields.Many2many('res.users', 'ev_pos_config_users', 'pos_config_id', 'x_user_id', string='User')
