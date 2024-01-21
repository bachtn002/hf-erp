# -*- coding: utf-8 -*-

from odoo import models
from odoo.exceptions import ValidationError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def write(self, vals):
        try:
            res = super(PosOrder, self).write(vals)
            if 'state' in vals and vals['state'] == 'paid' and not self.x_pos_order_refund_id and self.pos_channel_id.is_allow_send_zns:
                if self.x_home_delivery:
                    template = self.env['zns.template'].search(
                        [('template_type', '=', 'order_waiting_delivery'), ('status', '=', 'enable')], limit=1)
                    type_send_id = self.env['type.send.zns'].sudo().search(
                        [('code', '=', 'erp_hf'), ('active', '=', True)], limit=1)
                    val = {
                        'template_id': template.id,
                        'type': 'waiting_delivery',
                        'type_send_id': type_send_id.id,
                        'order_id': self.id,
                        'order_code': (self.sale_online + '/' + self.pos_reference) if self.sale_online else self.pos_reference,
                        'order_date': self.date_order,
                        'phone': self.partner_id.phone,
                        'customer_name': self.partner_id.name,
                        'order_value': self.amount_total,
                        'point_plus': self.loyalty_points,
                        'point_value': self.partner_id.loyalty_points,
                        'shop_id': self.x_pos_shop_id.id,
                        'shop_name': self.x_pos_shop_id.name,
                    }
                    zns_information = self.env['zns.information'].sudo().create(val)
                    zns_information.action_send_zns_sale_online()
            return res
        except Exception as e:
            raise ValidationError(e)
