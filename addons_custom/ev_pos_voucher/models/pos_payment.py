# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosPayment(models.Model):
    _inherit = "pos.payment"

    x_lot_id = fields.Many2one('stock.production.lot', string='Voucher')
    x_is_voucher_checked = fields.Boolean('Voucher Checked', default=False)

