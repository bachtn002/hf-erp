# -*- coding: utf-8 -*-

from odoo import models, fields


class PaymentCreateOrderQrcodeRes(models.Model):
    _name = 'payment.create.order.qrcode.res'
    _description = 'Payment Create Order QRCode Response'
    _rec_name = 'pg_order_reference'
    _order = 'id desc'

    response = fields.Text(string='Response')
    session_id = fields.Char(string='Session ID')
    pg_order_reference = fields.Char(string='PG Order Reference', index=True)
    time_sent_request_create_order = fields.Char(string='Time Sent Request')
    time_received_response_create_order = fields.Char(string='Time Received Response')
    