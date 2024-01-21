# -*- coding: utf-8 -*-

from odoo import models, fields
from odoo.exceptions import UserError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    pg_order_reference = fields.Char(string='Pg Order Reference', help='Mã tham chiếu giao dịch phía merchant')

    def write(self, vals):
        res = super(PosOrder, self).write(vals)
        if 'state' in vals and vals['state'] == 'paid':
            if not self.x_pos_order_refund_id:
                for item in self.payment_ids.payment_method_id:
                    if item.is_qrcode_payment:
                        val = {
                            'ip_request': '',
                            'response': {
                                'pos_session_id': self.session_id.id,
                                'order_id': self.id,
                                'order_reference': self.pos_reference.replace('-', ''),
                                'pos_shop_id': self.config_id.x_pos_shop_id.id
                            },
                            'type': 'log_checked_payment_result',
                        }
                        callback_payment_log = self.env['callback.payment.log'].sudo().create(val)
                        callback_payment_log.action_map_data_payment_qrcode()
                        break
        return res
