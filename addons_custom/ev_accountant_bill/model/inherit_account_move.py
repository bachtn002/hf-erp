# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_accountant_bill_id = fields.Many2one('accountant.bill', 'Accountant Bill')