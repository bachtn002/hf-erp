# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare


class StockProductionLotPrintStamp(models.TransientModel):
    _name = 'production.lot.print.stamp'
    _description = "Wizard production lot print stamps"

    production_lot_ids = fields.Many2many('production.lot.line', string="Lot detail")

    def default_get(self, fieldslist):
        res = super(StockProductionLotPrintStamp, self).default_get(fieldslist)
        context = self.env.context
        production_lot_ids = context and context.get('active_ids', [])
        productions = self.env['stock.production.lot'].browse(production_lot_ids)
        lot_line = []
        for production_lot in productions:
            production_lot.env['production.lot.line'].create({
                'name': production_lot.name,
                'product_id': production_lot.product_id.id,
                'product_uom_id': production_lot.product_id.uom_id.id,
                'expiration_date': production_lot.expiration_date,
                'number_of_codes': 1})

            line_val = (0, 0, {
                'name': production_lot.name,
                'product_id': production_lot.product_id.id,
                'product_uom_id': production_lot.product_id.uom_id.id,
                'expiration_date': production_lot.expiration_date,
                'number_of_codes': 1})
            lot_line.append(line_val)
        res.update({'production_lot_ids': lot_line})
        return res

    def print_stamp(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/ev_stock_picking.production_lot_print_stamp/%s' % self.id,
            'target': 'new', }


class ProductionLotLine(models.TransientModel):
    _name = 'production.lot.line'

    name = fields.Char('name')
    product_id = fields.Many2one('product.product', 'product')
    product_uom_id = fields.Many2one('uom.uom', 'uom_qty')
    expiration_date = fields.Date('Expiration Date')
    number_of_codes = fields.Integer('number of codes', default=1)
