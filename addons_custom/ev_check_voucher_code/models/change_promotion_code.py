# -*- coding: utf-8 -*-

from odoo import models, fields, _


class ChangeVoucherCode(models.Model):
    _name = 'change.promotion.code'
    _description = 'Change voucher code'

    name = fields.Char('Promotion Code')
    state_before = fields.Selection(selection=[
        ('new', 'New'),
        ('available', 'Available'),
        ('active', 'Active'),
        ('used', 'Used'),
        ('destroy', 'Destroy')
    ], default=None, string='State Promotion Before')
    state_after = fields.Selection(selection=[
        ('new', 'New'),
        ('available', 'Available'),
        ('active', 'Active'),
        ('used', 'Used'),
        ('destroy', 'Destroy')
    ], default=None, string='State Promotion After')
    promotion_use_code = fields.Integer('Promotion Use Code')
    promotion_use_code_old = fields.Integer('Promotion Use Code Old')
    user_change = fields.Char('Employee')
    datetime = fields.Char('Date')
