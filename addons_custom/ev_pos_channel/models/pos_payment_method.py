# -*- coding: utf-8 -*-

from odoo import models, fields


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    pos_channel_ids = fields.Many2many(comodel_name='pos.channel',
                                               relation='pos_channel_pos_payment_method_rel',
                                               column1='pos_payment_method_id', column2='pos_channel_id',
                                               string='Pos Channel')

