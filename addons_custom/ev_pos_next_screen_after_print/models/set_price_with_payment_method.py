import logging

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError


class SetPriceWithPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'
    is_cash_count_zero = fields.Boolean(string=_('Cash Zero'))
