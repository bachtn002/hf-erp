# -*- coding: utf-8 -*-

from odoo import models, fields
from odoo.exceptions import ValidationError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def write(self, vals):
        try:
            res = super(PosOrder, self).write(vals)
            if 'state' in vals and vals['state'] == 'paid':
                # Gọi API cập nhập trạng thái vận đơn
                if self.sale_online:
                    sale_online_order = self.env['sale.online'].search([('name', '=', self.sale_online)])
                    if sale_online_order.is_created_by_api:
                        if self.x_home_delivery and not self.x_pos_order_refund_id:
                            params = {
                                'orderNo': sale_online_order.ref_order,
                                'status': 'PROCESSING',
                            }
                            self._action_update_status_queue(params)
                        elif self.x_pos_order_refund_id:
                            params = {
                                'orderNo': sale_online_order.ref_order,
                                'status': 'RETURNED',
                            }
                            self._action_update_status_queue(params)
                        else:
                            params = {
                                'orderNo': sale_online_order.ref_order,
                                'status': 'COMPLETED',
                            }
                            self._action_update_status_queue(params)
            return res
        except Exception as ex:
            raise ValidationError(ex)

    def _action_update_status_queue(self, params):
        val = {
            'params': str(params)
        }
        sync_state_miniapp = self.env['sync.state.miniapp'].sudo().create(val)
        sync_state_miniapp.action_update_status_shipping()
