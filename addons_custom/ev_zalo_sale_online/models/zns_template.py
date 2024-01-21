# -*- coding: utf-8 -*-

from odoo import fields, models


class ZnsTemplate(models.Model):
    _inherit = 'zns.template'

    template_type = fields.Selection([
        ('otp', 'OTP'),
        ('order_online_confirm', 'Order Online Confirm'),
        ('order_waiting_delivery', 'Order Waiting Delivery'),
        ('order_delivery', 'Order Delivery'),
        ('send_promotion', 'Send Promotion'),
        ('rating_service', 'Rating Service'),
        ('mini_game', 'Mini Game'),
        ('thanks_for_purchase', 'Thanks For Purchase')
    ], string='Template Type', default=None)
