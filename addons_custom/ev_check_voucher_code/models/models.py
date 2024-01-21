# -*- coding: utf-8 -*-

from odoo import models, fields, _


class VoucherCode(models.Model):
    _name = 'change.voucher.code'
    _description = 'Change voucher code'

    name = fields.Char(_('Voucher Code'))
    state_before = fields.Char(_('State voucher before'))
    state_after = fields.Char(_('State voucher after'))
    user_change = fields.Char('Employee')
    datetime = fields.Char('Date')
