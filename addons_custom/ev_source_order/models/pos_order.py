# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class PosOrder(models.Model):
    _inherit = 'pos.order'

    x_source_order_id = fields.Many2one('source.order', 'Source Order')
    x_home_delivery = fields.Boolean('Home Delivery', default=False)
    x_receiver = fields.Char('Receiver')
    x_partner_phone = fields.Char('Partner Phone')
    x_address_delivery = fields.Char('Address Delivery')
    x_lat = fields.Char('Latitude')
    x_long = fields.Char('Longitude')
    x_ship_type = fields.Selection([
        ('internal', 'Internal'),
        ('other', 'Other'),
    ], 'Ship Type', default=None)

    @api.model
    def _order_fields(self, ui_order):
        result = super(PosOrder, self)._order_fields(ui_order)
        result['x_source_order_id'] = ui_order.get('x_source_order_id', '')
        return result

