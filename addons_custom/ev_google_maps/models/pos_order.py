# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    x_ship_note = fields.Char('Ship Note')
    x_cod = fields.Float('COD Fee')
    x_distance = fields.Float('Distance Delivery')

    @api.model
    def _order_fields(self, ui_order):
        result = super(PosOrder, self)._order_fields(ui_order)
        result['x_home_delivery'] = ui_order.get('x_home_delivery')
        if ui_order.get('x_home_delivery') and ui_order.get('partner_id'):
            result['x_address_delivery'] = ui_order.get('x_address_delivery', '')
            result['x_lat'] = ui_order.get('x_lat', '')
            result['x_long'] = ui_order.get('x_long', '')
            result['x_ship_type'] = ui_order.get('x_ship_type', '')
            result['x_ship_note'] = ui_order.get('x_ship_note', '')
            result['x_partner_phone'] = ui_order.get('x_partner_phone', '')
            result['x_receiver'] = ui_order.get('x_receiver', '')
            result['x_cod'] = ui_order.get('x_cod', '')
            result['x_distance'] = ui_order.get('x_distance', '')
        return result
