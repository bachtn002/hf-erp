# -*- coding: utf-8 -*-

from odoo import models
from odoo.exceptions import ValidationError


class SaleOnline(models.Model):
    _inherit = 'sale.online'

    def send_sale_request(self):
        try:
            res = super(SaleOnline, self).send_sale_request()
            zns_infor_obj = self.env['zns.information'].search([('order_code', '=', self.name), ('state', '=', 'done')], limit=1)
            if not zns_infor_obj and self.pos_channel_id.is_allow_send_zns:
                template = self.env['zns.template'].search(
                    [('template_type', '=', 'order_online_confirm'), ('status', '=', 'enable')], limit=1)
                type_send_id = self.env['type.send.zns'].sudo().search([('code', '=', 'erp_hf'), ('active', '=', True)],
                                                                       limit=1)
                tracking_id = self.name
                val = {
                    'template_id': template.id,
                    'type': 'sale_online',
                    'type_send_id': type_send_id.id,
                    'phone': self.phone,
                    'order_date': self.date,
                    'order_code': self.name,
                    'customer_name': self.customer,
                    'order_value': self.amount_total,
                    'shop_name': self.pos_config_id.name,
                    'tracking_id': tracking_id
                }
                zns_information = self.env['zns.information'].sudo().create(val)
                zns_information.action_send_zns_sale_online()
                return res
        except Exception as e:
            raise ValidationError(e)
