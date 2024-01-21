# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.exceptions import ValidationError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def write(self, vals):
        try:
            # Cập nhật điểm khách hàng sau đó gửi tin nhắn
            res = super(PosOrder, self).write(vals)
            if 'state' in vals and vals['state'] == 'paid':
                self.create_loyalty_point_history()
                if not self.x_pos_order_refund_id and not self.x_home_delivery and self.pos_channel_id.is_allow_send_zns:
                    oa_id = self.x_pos_shop_id.x_oa_id
                    app_id = self.x_pos_shop_id.x_app_id
                    tmpl_id = self.x_pos_shop_id.x_template_id
                    template_id = self.env['zns.template'].sudo().search(
                        [('template_id', '=', tmpl_id), ('oa_id', '=', oa_id), ('app_id', '=', app_id)],
                        limit=1)
                    type_send_id = self.env['type.send.zns'].sudo().search([('code', '=', 'erp_hf'), ('active', '=', True)],
                                                                           limit=1)
                    if self.partner_id.phone and template_id and type_send_id and oa_id and app_id:
                        value = {
                            'template_id': template_id.id,
                            'type': 'order',
                            'type_send_id': type_send_id.id,
                            'order_id': self.id,
                            'order_code': self.pos_reference,
                            'order_date': self.date_order,
                            'phone': self.partner_id.phone,
                            'customer_name': self.partner_id.name,
                            'order_value': self.amount_total,
                            'point_plus': self.loyalty_points,
                            'point_value': self.partner_id.loyalty_points,
                            'shop_id': self.x_pos_shop_id.id,
                            'shop_name': self.x_pos_shop_id.name,
                        }
                        zns_information = self.env['zns.information'].sudo().create(value)
                        zns_information.action_send_zns()
            return res
        except Exception as e:
            raise ValidationError(e)
