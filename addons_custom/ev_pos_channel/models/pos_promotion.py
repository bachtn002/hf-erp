# -*- coding: utf-8 -*-

from odoo import models, fields


class PosPromotion(models.Model):
    _inherit = 'pos.promotion'

    pos_channel_ids = fields.Many2many('pos.channel', string='Pos Channel')
