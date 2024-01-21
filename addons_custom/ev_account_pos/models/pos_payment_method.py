# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    x_is_cash_method = fields.Boolean('Is Cash Method')