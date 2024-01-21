# -*- coding: utf-8 -*-
import datetime

from odoo import fields, models, api


class CashStatement(models.Model):
    _name = 'cash.statement'

    pos_session_id = fields.Many2one('pos.session', string='pos session', readonly=True)

    date = fields.Date(string='date', required=True, default=fields.Date.today)
    denominations = fields.Integer(string='denominations', readonly=True)
    quantity = fields.Integer(string='quantity')
    amount = fields.Float(string='amount', compute='_compute_amount')

    @api.onchange('quantity')
    def _compute_amount(self):
        for record in self:
            record.amount = record.denominations * record.quantity
