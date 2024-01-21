# -*- coding: utf-8 -*-
import odoo.tools.config as config

from odoo import models, fields, api, exceptions
from datetime import datetime


class ReportPosPaymentMethod(models.TransientModel):
    _name = 'report.pos.payment.method.line'

    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    pos_payment_method_id = fields.Many2one('pos.payment.method', string='Payment Method')
    intital_balance = fields.Float('Intital balance')
    debit = fields.Float('Debit')
    credit = fields.Float('Credit')
    balance = fields.Float('Balance', compute='_compute_balance')
    report_pos_payment_method_id = fields.Many2one('report.pos.payment.method', string='Report Pos Payment Method')

    @api.depends('intital_balance', 'debit', 'credit')
    def _compute_balance(self):
        for record in self:
            record.balance = record.intital_balance + record.debit - record.credit
