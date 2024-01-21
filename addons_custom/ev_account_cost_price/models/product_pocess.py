# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError, except_orm
from odoo.osv import osv


class ProductProcessDetail(models.Model):
    _inherit = "product.process.detail"

    amount = fields.Float('Amount')


class ProductProcessLine(models.Model):
    _inherit = "product.process.line"

    amount = fields.Float('Amount')


class ProductProcess(models.Model):
    _inherit = 'product.process'

    def _get_product_process(self, process_line_id, move_ids):
        rule_process_id = process_line_id.rule_id
        amount = 0
        for from_id in process_line_id.from_detail_ids:
            for move_id in move_ids.filtered(lambda t: t.product_id.id == from_id.product_id.id and t.product_qty == from_id.qty):
                amount += abs(move_id.x_value)
                from_id.amount = abs(move_id.x_value)
                break
        for to_id in process_line_id.to_detail_ids:
            for to_rule_id in rule_process_id.to_rule_ids.filtered(lambda t: t.product_id.id == to_id.product_id.id):
                to_id.amount = round(amount * to_rule_id.percent/100,0)
                break
        process_line_id.amount = amount

    def _action_compare_cost(self):
        move_list = []
        for line in self.process_line_ids:
            amount = 0
            for stock_move in line.picking_out_id.move_lines:
                amount += abs(stock_move.x_value)
                process_detail_id = self.env['product.process.detail'].sudo().search([('from_process_id','=',line.id),('product_id','=',stock_move.product_id.id)], limit=1)
                if process_detail_id:
                    process_detail_id.amount = abs(stock_move.x_value)
            line.amount = amount
            amount_tmp = 0
            for process_to_id in line.to_detail_ids:
                process_to_id.amount = round(amount*process_to_id.percent/100,0)
                amount_tmp += round(amount*process_to_id.percent/100,0)
                stock_move_to = self.env['stock.move'].sudo().search([('picking_id','=', line.picking_in_id.id),('product_id','=',process_to_id.product_id.id)], limit=1)
                if stock_move_to:
                    stock_move_to.update({
                        'x_unit_cost': process_to_id.amount / process_to_id.qty,
                        'x_value': process_to_id.amount
                    })
                    self.env.cr.commit()
                    move_list.append(stock_move_to.id)
            if amount != amount_tmp:
                process_detail_id = self.env['product.process.detail'].sudo().search([('to_process_id','=',line.id)], order='percent desc', limit=1)
                if amount_tmp > amount:
                    process_detail_id.amount = process_detail_id.amount - (amount_tmp-amount)
                    stock_move_tmp = self.env['stock.move'].sudo().search([('picking_id','=', line.picking_in_id.id),('product_id','=',process_detail_id.product_id.id)], limit=1)
                    stock_move_tmp.update({
                        'x_unit_cost': process_detail_id.amount / process_detail_id.qty,
                        'x_value': process_detail_id.amount
                    })
                    self.env.cr.commit()
                elif amount_tmp < amount:
                    process_detail_id.amount = process_detail_id.amount + (amount - amount_tmp)
                    stock_move_tmp = self.env['stock.move'].sudo().search([('picking_id', '=', line.picking_in_id.id), ('product_id', '=', process_detail_id.product_id.id)], limit=1)
                    stock_move_tmp.update({
                        'x_unit_cost': process_detail_id.amount / process_detail_id.qty,
                        'x_value': process_detail_id.amount
                    })
                    self.env.cr.commit()
        return move_list


