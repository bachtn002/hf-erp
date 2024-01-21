# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    pos_channel_id = fields.Many2one('pos.channel', string='Pos Channel')

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res['pos_channel_id'] = int(ui_order.get('x_id_pos_channel'))
        return res
