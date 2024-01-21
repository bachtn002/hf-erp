# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, except_orm
from odoo.osv import osv
import xlrd
import base64
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class ImportAccountBalance(models.TransientModel):
    _name = 'run.create.account.move'

    from_date = fields.Date('From date')
    to_date = fields.Date('to date')

    # def action_run(self):
    #     sql = """
    #         select id from stock_move where state = 'done' and company_id = 2
    #         and id not in (select stock_move_id from account_move where stock_move_id is not null)
    #         and purchase_line_id is null and date::date > '2021-03-01'
    #         order by date
    #     """
    #     self.env.cr.execute(sql)
    #     stock_move_dict = self.env.cr.dictfetchall()
    #     stock_move_list =[]
    #     for item in stock_move_dict:
    #         stock_move_list.append(item['id'])
    #     stock_move_ids = self.env['stock.move'].sudo().search([('id','in', stock_move_list)])
    #     for move_id in stock_move_ids:
    #         move_id._compute_cost()
    #         qty = 0
    #         for move_line_id in move_id.move_line_ids:
    #             qty += move_line_id.qty_done
    #             move_line_id._compute_cost()
    #         if move_id.product_qty != qty or move_id.product_qty != move_id.quantity_done:
    #             raise UserError(_('Số lượng move khác số lượng move_line %s' %move_id.id))
    #         unit_cost = move_id.x_unit_cost
    #         value = move_id.x_value
    #         quantity = qty if move_id.location_dest_id.usage == 'internal' else -(qty)
    #         stock_valuation_layer_id = self.env['stock.valuation.layer'].sudo().search([('stock_move_id', '=', move_id.id)],limit=1)
    #         stock_valuation_layer_id.update({
    #             'unit_cost': unit_cost,
    #             'value': value,
    #             'quantity': quantity,
    #         })
    #         move_id._account_entry_move(move_id.product_qty, move_id.name, stock_valuation_layer_id.id, stock_valuation_layer_id.value)


    # def action_run(self):
    #     error_list = ''
    #     stock_move_ids = self.env['stock.move'].sudo().search([('inventory_id','=',False),('purchase_line_id','=',False),('state','=','done')])
    #     for stock_move_id in stock_move_ids:
    #         try:
    #             if len(stock_move_id.account_move_ids) != 1:
    #                 raise UserError('Multi account move %s' %stock_move_id.id)
    #             account_move_id = stock_move_id.account_move_ids[0].id
    #             is_in = stock_move_id.location_dest_id.usage == 'internal'
    #             if is_in:
    #                 if stock_move_id.x_value < 0:
    #                     raise UserError('x_value < 0 %s' % stock_move_id.id)
    #                 quantity = stock_move_id.product_qty
    #                 balance = stock_move_id.x_value
    #                 sql = """
    #                     UPDATE account_move_line a
    #                     SET quantity = %s, debit = %s, balance = %s, amount_currency = %s, credit = 0
    #                     WHERE a.move_id = %s AND a.account_id = 800;
    #                     UPDATE account_move_line a
    #                     SET quantity = %s, credit = %s, balance = %s, amount_currency = %s, debit = 0
    #                     WHERE a.move_id = %s AND a.account_id != 800;
    #                     UPDATE account_move a
    #                     SET amount_total = %s, amount_total_signed = %s
    #                     WHERE a.id = %s
    #                 """
    #                 self._cr.execute(sql, (quantity,balance,balance,balance,account_move_id,
    #                                        quantity,balance,-balance,-balance, account_move_id,
    #                                        balance,balance,account_move_id,))
    #             else:
    #                 if stock_move_id.x_value > 0:
    #                     raise UserError('x_value > 0 %s' % stock_move_id.id)
    #                 quantity = -stock_move_id.product_qty
    #                 balance = abs(stock_move_id.x_value)
    #                 sql = """
    #                     UPDATE account_move_line a
    #                     SET quantity = %s, debit = %s, balance = %s, amount_currency = %s, credit = 0
    #                     WHERE a.move_id = %s AND a.account_id != 800;
    #                     UPDATE account_move_line a
    #                     SET quantity = %s, credit = %s, balance = %s, amount_currency = %s, debit = 0
    #                     WHERE a.move_id = %s AND a.account_id = 800;
    #                     UPDATE account_move a
    #                     SET amount_total = %s, amount_total_signed = %s
    #                     WHERE a.id = %s
    #                 """
    #                 self._cr.execute(sql, (quantity, balance, balance, balance, account_move_id,
    #                                        quantity, balance, -balance, -balance, account_move_id,
    #                                        balance, balance, account_move_id,))
    #         except ValueError as e:
    #             error_list = error_list + "- %s \n" % (e)
    #             continue
    #     if error_list:
    #         raise UserError(_(error_list))


    def action_run(self):
        account_move_ids = self.env['account.move'].search([('state', '=', 'posted'), ('date', '>=', self.from_date), ('date', '<=', self.to_date)])
        for move in account_move_ids:
            move._update_contra_account_id()


