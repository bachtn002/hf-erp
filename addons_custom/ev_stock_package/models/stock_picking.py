# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    total_package_number = fields.Integer("Total Package", default=0)

    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        if self.id != False:
            out_stock_transfer = self.env['stock.transfer'].search([('out_picking_id','=',self.id)],limit=1)
            if out_stock_transfer:
                for pack in out_stock_transfer.package_lines:
                    if pack.qty_out != pack.qty:
                        raise UserError(_('Quantity out must be equal to quantity package'))
            in_stock_transfer = self.env['stock.transfer'].search([('in_picking_id', '=', self.id)], limit=1)
            if in_stock_transfer:
                for pack in in_stock_transfer.package_lines:
                    if pack.qty_in != pack.qty:
                        raise UserError(_('Quantity in must be equal to quantity package'))
        return res