# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import time
from odoo.exceptions import ValidationError, except_orm


class SupplyRequestLine(models.Model):
    _name = 'supply.request.line'
    _description = 'Supply Request Detail'

    supply_request_id = fields.Many2one('supply.request', string='Supply Request', ondelete='cascade')
    request_line_id = fields.Many2one('sale.request.line', 'Sale Request Detail')
    product_id = fields.Many2one('product.product', string='Product', domain=[('type', 'in', ['product', 'consu'])], index=True, required=True)
    uom_id = fields.Many2one('uom.uom', string='Uom')
    warehouse_dest_id = fields.Many2one('stock.warehouse','Destination Warehouse')
    purchase_order_id = fields.Many2one('purchase.order', 'Purchase Order')
    partner_id = fields.Many2one('res.partner', 'Partner')
    qty_request = fields.Float('Quantity Request', digits='Product Unit of Measure')
    qty_buy = fields.Float('Quantity Buy', digits='Product Unit of Measure')
    qty_in = fields.Float('Quantity In', digits='Product Unit of Measure', readonly=True)
    price_unit = fields.Float('Price Unit')
    categ_id = fields.Many2one('product.category', 'Category')
    note = fields.Text('Note')
