# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountJournalGeneralInherit(models.Model):
    _inherit = 'account.journal.general'

    picking_id = fields.Many2one('stock.picking', string="Stock Picking Ref", index=True, ondelete="cascade")
