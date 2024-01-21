# -*- coding: utf-8 -*-

from odoo import models, fields


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    is_qrcode_payment = fields.Boolean(string='Is QRCode Payment')
