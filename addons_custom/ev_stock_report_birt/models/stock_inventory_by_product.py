# -*- coding: utf-8 -*-

from odoo import models, fields, api,_, exceptions
from odoo.exceptions import UserError
try:
    import cStringIO as stringIOModule
except ImportError:
    try:
        import StringIO as stringIOModule
    except ImportError:
        import io as stringIOModule
from datetime import datetime, timedelta
import xlwt
import base64


class EvInventoryProduct(models.TransientModel):
    _name = 'stock.inventory.by.product'

    name = fields.Char('Product')
    total_quantity = fields.Float('Total quantity', compute='_compute_total', digits='Product Unit of Measure')
    inventory_ids = fields.One2many('stock.inventory.by.product.line', 'inventory_id', "Check Inventory")

    def _compute_total(self):
        for s in self:
            total_quantity = 0.0
            for line in s.inventory_ids:
                total_quantity += line.quantity
            s.total_quantity = total_quantity

    def action_check(self):
        self.inventory_ids.unlink()
        if self.name == False:
            return
        lines = []
        # if len(self.name) < 5:
        #     raise except_orm(_('Thông báo'), _('Xin hãy nhập mã sản phẩm lớn hơn 5 ký tự'))
        product_ids = self.env['product.product'].search(
            [('default_code', 'ilike', '%' + self.name + '%')])
        if not product_ids:
            product_ids = self.env['product.product'].search(
                [('name', 'ilike',self.name + '%')])
        if len(product_ids) < 1:
            raise UserError(_('Notification! Product code not found!'))
        else:
            quantity_all = 0
            for product_id in product_ids:
                warehouse_ids = self.env['stock.warehouse'].search([('active','=',True)])
                for warehouse in warehouse_ids:
                    qty = 0
                    total_availability = self.env['stock.quant']._get_available_quantity(product_id, warehouse.lot_stock_id)
                    qty = qty + total_availability
                    quantity_all = quantity_all + total_availability

                    if qty != 0:
                        argvs = {
                            'product_id': product_id.id,
                            'warehouse_id': warehouse.id,
                            'quantity': qty,
                            'price_unit': product_id.lst_price,
                            'inventory_id': self.id,
                        }
                        lines.append([0, 0, argvs])
        if quantity_all == 0:
            raise UserError(_('Notification! The product is no available in Stock!'))
        self.inventory_ids = lines


class IziInventoryProductLine(models.TransientModel):
    _name = 'stock.inventory.by.product.line'

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    product_id = fields.Many2one('product.product', string='Product')
    price_unit = fields.Float('Price unit')
    quantity = fields.Float('Quantity', digits='Product Unit of Measure')
    inventory_id = fields.Many2one('stock.inventory.by.product', "Check Inventory")




