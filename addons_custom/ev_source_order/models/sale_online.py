# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class SaleOnline(models.Model):
    _inherit = 'sale.online'

    source_order_id = fields.Many2one('source.order', 'Source Order', search='_search_source')
    home_delivery = fields.Boolean('Home Delivery', default=False)
    receiver = fields.Char('Receiver')
    receiver_phone = fields.Char('Receiver Phone')
    address_delivery = fields.Char('Address Delivery')
    lat = fields.Char('Latitude')
    long = fields.Char('Longitude')

