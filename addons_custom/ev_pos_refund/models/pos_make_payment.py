# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    def _default_payment_method(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            order_id = self.env['pos.order'].browse(active_id)
            payment_method_id = self.env['pos.payment']
            if order_id:
                check = False
                for payment in order_id.x_pos_order_refund_id.payment_ids:
                    if payment.payment_method_id.is_cash_count:
                        payment_method_id = payment.payment_method_id
                        check = True
                        break
                if check == False:
                    for payment in order_id.x_pos_order_refund_id.payment_ids:
                        payment_method_id = payment.payment_method_id
                        break
            return payment_method_id.id
        return False

    payment_method_id = fields.Many2one('pos.payment.method', string='Payment Method', required=True,
                                        default=_default_payment_method)
