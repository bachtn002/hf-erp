# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        try:
            for record in self:
                picking_id = self.env['stock.picking'].search([('name', '=', record.ref)])
                if picking_id:
                    for line in record.line_ids:
                        line.x_account_expense_item_id = picking_id.x_account_expense_item
        except Exception as e:
            raise ValidationError(e)
        return super(AccountMove, self)._post(soft)
