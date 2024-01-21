# -*- coding: utf-8 -*-

from odoo import models, fields
from datetime import datetime


class PosSession(models.Model):
    _inherit = 'pos.session'

    def action_pos_session_closing_control_queue(self):
        res = super(PosSession, self).action_pos_session_closing_control_queue()
        lot_series = []
        # Loại bỏ đơn trả hàng trong phiên
        orders = self.order_ids.search([('session_id', '=', self.id), ('x_pos_order_refund_id', '=', False)])
        orders_return = self.order_ids.search(
            [('session_id', '=', self.id), ('x_pos_order_refund_id', '!=', False)]).mapped('x_pos_order_refund_id')

        orders_release = orders - orders_return

        lens = len(orders_release)
        number_per_lot = self.env.company.number_pos_per_lot
        lot_qty = lens // number_per_lot
        j = lot_qty
        i = 0
        while j > 0:
            lot_series.append(orders_release[i:i + number_per_lot])
            i += number_per_lot
            j -= 1
            lens -= number_per_lot
        if lens > 0:
            lot_series.append(orders_release[lot_qty * number_per_lot:])
        for item in lot_series:
            val = {
                'action_type': 'release',
                'session_id': self.id,
                'line_ids': item
            }
            sinvoice_lot = self.env['create.sinvoice.lot'].sudo().create(val)
            sinvoice_lot.action_api_release_sinvoice()
        return res
