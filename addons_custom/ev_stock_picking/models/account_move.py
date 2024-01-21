# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from collections import defaultdict


class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    # def _set_args_journal_general(self, debit, credit, default=True, amountt=0):
    #     result = super(AccountMoveInherit, self)._set_args_journal_general(debit, credit, default=default,
    #                                                                        amountt=amountt)
    #     if self.stock_move_id and self.stock_move_id.picking_id:
    #         result['picking_id'] = self.stock_move_id.picking_id.id
    #     for stock_picking_id in self.stock_picking_ids:
    #         if stock_picking_id.picking_type_id.code == 'incoming':
    #             result['picking_id'] = stock_picking_id.id
    #     return result
