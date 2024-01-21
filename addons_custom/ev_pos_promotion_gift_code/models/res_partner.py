# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_pos_promotion_gift_code_history_ids = fields.One2many('pos.promotion.gift.code.history', 'partner_id',
                                                            'Gift Code History')
