# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class StockProductPrintStamp(models.TransientModel):
    _name = 'product.product.print.stamp'
    _description = "Wizard product print stamps"

    product_ids = fields.Many2many('product.line', string="Product detail")

    def default_get(self, fieldslist):
        res = super(StockProductPrintStamp, self).default_get(fieldslist)
        context = self.env.context
        product_ids = context and context.get('active_ids', [])
        products = self.env['product.template'].browse(product_ids)
        product_line = []
        for product_id in products:
            product_id.env['product.line'].create({
                'name': product_id.name,
                'barcode': product_id.barcode,
                'default_code': product_id.default_code,
                'product_uom_id': product_id.uom_id.id,
                'number_of_codes': 1})

            line_val = (0, 0, {
                'name': product_id.name,
                'barcode': product_id.barcode,
                'default_code': product_id.default_code,
                'product_uom_id': product_id.uom_id.id,
                'number_of_codes': 1})
            product_line.append(line_val)
        res.update({'product_ids': product_line})
        return res

    def print_stamp(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/ev_stock_picking.product_product_print_stamp/%s' % self.id,
            'target': 'new', }


class ProductLine(models.TransientModel):
    _name = 'product.line'

    name = fields.Char('name')
    barcode = fields.Char('barcode')
    default_code = fields.Char('default code')
    product_uom_id = fields.Many2one('uom.uom', 'uom_qty')
    number_of_codes = fields.Integer('number of codes', default=1)
