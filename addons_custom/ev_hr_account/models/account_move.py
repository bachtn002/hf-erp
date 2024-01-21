# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_personnel_expenses_id = fields.Many2one('account.personnel.expenses', 'Personnel Expenses')

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_fee_item_id = fields.Many2one('account.expense.item', 'Personnel Expenses')
    x_part_id = fields.Many2one('res.partner', 'Part')