# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosUser(models.Model):
    _inherit = 'res.users'

    x_pos_config_ids = fields.Many2many('pos.config', 'ev_pos_config_users', 'x_user_id', 'pos_config_id', string='Pos config')
