# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _action_done(self):
        try:
            res = super(StockPicking, self)._action_done()
            stock_transfer = self.env['stock.transfer'].search([('out_picking_id', '=', self.id)], limit=1)
            if self.x_type_transfer == 'out_transfer' and stock_transfer:
                if stock_transfer.x_ship_type != 'no':
                    if stock_transfer.x_ship_type == 'other' and not stock_transfer.company_id.x_call_ship:
                        raise UserError(_('The system does not allow calling to ship outside'))
                    stock_transfer.action_create_delivery()
            return res
        except Exception as e:
            raise ValidationError(e)
