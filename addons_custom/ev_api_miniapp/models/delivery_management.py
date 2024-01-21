# -*- coding: utf-8 -*-

from odoo import models, fields
from odoo.exceptions import ValidationError


class DeliveryManagement(models.Model):
    _inherit = 'delivery.management'

    def write(self, vals):
        try:
            res = super(DeliveryManagement, self).write(vals)
            if 'state' in vals and vals['state'] == 'done':
                if self.order_id and self.order_id.sale_online:
                    sale_online_order = self.env['sale.online'].search([('pos_order_id', '=', self.order_id.id)])
                    if sale_online_order.is_created_by_api:
                        params = {
                            'orderNo': sale_online_order.ref_order,
                            'status': 'COMPLETED',
                        }
                        val = {
                            'params': str(params)
                        }
                        sync_state_miniapp = self.env['sync.state.miniapp'].sudo().create(val)
                        sync_state_miniapp.action_update_status_shipping()
            return res
        except Exception as ex:
            raise ValidationError(ex)
