# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, except_orm
from odoo.tools import float_is_zero
from datetime import datetime


class StockMove(models.Model):
    _inherit = 'stock.move'

    x_note_in_out_comming = fields.Char(string='Note')

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id,
                                       credit_account_id, description):
        res = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value,
                                                                    debit_account_id, credit_account_id, description)
        if not self.picking_id or not self.picking_id.x_analytic_account_id:
            return res
        analytic_account_vals = {
            'analytic_account_id': self.picking_id.x_analytic_account_id.id
        }
        res['credit_line_vals'].update(analytic_account_vals)
        res['debit_line_vals'].update(analytic_account_vals)
        if credit_value != debit_value:
            res['price_diff_line_vals'].update(analytic_account_vals)
        return res

