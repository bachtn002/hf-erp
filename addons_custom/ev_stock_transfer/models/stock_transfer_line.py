# -*- coding: utf-8 -*-


from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import ValidationError, except_orm
from odoo.exceptions import UserError


class StockTransferLine(models.Model):
    _name = 'stock.transfer.line'
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', 'Product', domain=[('type', 'in', ['product', 'consu'])])
    name = fields.Char('Product name')
    quantity = fields.Float('Quantity', digits='Product Unit of Measure')
    qty_available = fields.Char('Status', digits='Product Unit of Measure')
    in_quantity = fields.Float('In Quantity', digits='Product Unit of Measure')
    out_quantity = fields.Float('Out Quantity', digits='Product Unit of Measure')
    available_qty = fields.Float('Available Quantity', digits='Product Unit of Measure', readonly=True)
    product_uom = fields.Many2one('uom.uom', 'Unit of Measure', required=True)
    stock_transfer_id = fields.Many2one('stock.transfer', 'Stock transfer')
    note = fields.Text('Note')
    state = fields.Selection([('not_available', 'Not Available'), ('available', 'Available')],'State')

    @api.onchange('product_id')
    def onchange_product_id(self):
        product = self.product_id.with_context(lang=self.env.user.lang)
        self.name = product.partner_ref
        self.product_uom = product.uom_id.id
        return {'domain': {'product_uom': [('category_id', '=', product.uom_id.category_id.id)]}}

    def _create_stock_moves(self, picking, transfer):
        moves = self.env['stock.move']
        for line in self:
            if transfer:
                vals = line._prepare_stock_moves(picking, transfer)
                move_id = moves.create(vals)
                move_id.x_out_transfer_line_id = line.id
            else:
                vals = line._prepare_stock_moves_in(picking, transfer)
                move_id = moves.create(vals)
                move_id.x_in_transfer_line_id = line.id

    def _prepare_stock_moves(self, picking, transfer=True):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        template = {
            'name': self.name or '',
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'product_uom_qty': self.quantity if not self.out_quantity else self.out_quantity,
            'date': self.stock_transfer_id.date if transfer else fields.Datetime.now(),
            'date_deadline': self.stock_transfer_id.date if transfer else fields.Datetime.now(),
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'picking_id': picking.id,
            'state': 'draft',
            'company_id': self.stock_transfer_id.company_id.id,
            'picking_type_id': picking.picking_type_id.id,
            'origin': self.stock_transfer_id.name,
            'route_ids': (picking.picking_type_id.warehouse_id and [
                (6, 0, [x.id for x in picking.picking_type_id.warehouse_id.route_ids])] or []),
            'warehouse_id': picking.picking_type_id.warehouse_id.id,
        }
        res.append(template)
        return res

    def _prepare_stock_moves_in(self, picking, transfer=True):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        template = {
            'name': self.name or '',
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'product_uom_qty': self.out_quantity,
            'date': self.stock_transfer_id.date if transfer else fields.Datetime.now(),
            'date_deadline': self.stock_transfer_id.date if transfer else fields.Datetime.now(),
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'picking_id': picking.id,
            'state': 'draft',
            'company_id': self.stock_transfer_id.company_id.id,
            'picking_type_id': picking.picking_type_id.id,
            'origin': self.stock_transfer_id.name,
            'route_ids': (picking.picking_type_id.warehouse_id and [
                (6, 0, [x.id for x in picking.picking_type_id.warehouse_id.route_ids])] or []),
            'warehouse_id': picking.picking_type_id.warehouse_id.id,
        }
        res.append(template)
        return res

