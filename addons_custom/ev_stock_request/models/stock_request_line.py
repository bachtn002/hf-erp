# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo import time
from odoo.exceptions import ValidationError, except_orm, UserError



class StockRequestLine(models.Model):
    _name = 'stock.request.line'
    _description = 'Stock Request Detail'

    request_id = fields.Many2one('stock.request', string='Request', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', domain=[('type', 'in', ['product', 'consu'])],
                                 index=True, required=True)
    uom_id = fields.Many2one('uom.uom', string='Uom')
    qty = fields.Float('Quantity Request', digits='Product Unit of Measure')
    qty_apply = fields.Float('Quantity Apply', digits='Product Unit of Measure')
    note = fields.Text('Note')
    price_unit = fields.Float('Price Unit')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.product_tmpl_id.uom_id.id

    def _create_stock_moves(self, picking, transfer):
        moves = self.env['stock.move']
        for line in self:
            if transfer:
                vals = line._prepare_stock_moves(picking, transfer)
                move_id = moves.create(vals)

    def _prepare_stock_moves(self, picking, transfer=True):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        template = {
            'name': self.product_id.name or '',
            'product_id': self.product_id.id,
            'product_uom': self.uom_id.id,
            'product_uom_qty': self.qty,
            'date': fields.Datetime.now(),
            'date_deadline': fields.Datetime.now(),
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'picking_id': picking.id,
            'price_unit': self.price_unit if self.price_unit else 0,
            'state': 'draft',
            'company_id': self.request_id.company_id.id,
            'picking_type_id': picking.picking_type_id.id,
            'origin': self.request_id.name,
            'route_ids': (picking.picking_type_id.warehouse_id and [
                (6, 0, [x.id for x in picking.picking_type_id.warehouse_id.route_ids])] or []),
            'warehouse_id': self.request_id.warehouse_dest_id.id,
        }
        res.append(template)
        return res
