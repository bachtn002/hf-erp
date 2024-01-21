# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class StockCardLine(models.TransientModel):
    _name = 'stock.card.line'

    stock_card_id = fields.Many2one('stock.card')
    move_id = fields.Many2one('stock.move', "Stock move")
    date = fields.Date("Date")
    reference = fields.Char("Reference")
    picking_name = fields.Char("Picking")
    note = fields.Char("Note")
    qty_in = fields.Float("Qty in", digits='Product Unit of Measure')
    qty_out = fields.Float("Qty out", digits='Product Unit of Measure')
    qty_inventory = fields.Float("Qty Inventory", digits='Product Unit of Measure')
    x_description = fields.Char("Type")
    partner_name = fields.Char("Partner name")
    user = fields.Char("User")
