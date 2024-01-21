# -*- coding: utf-8 -*-

from odoo import models, fields, api,_


class StockMove(models.Model):
    _inherit = 'stock.move'

    x_out_transfer_line_id = fields.Many2one('stock.transfer.line', 'Out Transfer Line')
    x_in_transfer_line_id = fields.Many2one('stock.transfer.line', 'In Transfer Line')