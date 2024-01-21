# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date, datetime, timedelta


class PosOrderRefund(models.Model):
    _inherit = 'pos.order'

    x_is_auto_approve = fields.Boolean('Is Auto Approve')

    def _auto_approve_refund(self):
        order_refund = self.env['pos.order'].search(
            [('x_pos_send_return', '=', True),
             ('x_allow_return', '=', False),
             ('date_order', '>=',
              datetime.combine(date.today(), datetime.min.time()) - timedelta(
                  hours=7))])

        if order_refund:
            order_refund.write({'x_allow_return': True, 'x_is_auto_approve': True})