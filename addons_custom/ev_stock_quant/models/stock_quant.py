# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.float_utils import float_compare, float_is_zero


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def _update_reserved_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None,strict=False):
        self = self.sudo()
        rounding = product_id.uom_id.rounding
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                              strict=strict)
        if len(quants) == 0:
            self.create({
                'product_id': product_id.id,
                'location_id': location_id.id,
                'lot_id': lot_id.id or None,
                'company_id': location_id.company_id.id,
                'quantity': 0,
                'reserved_quantity': abs(quantity)
            })
        if float_compare(quantity, 0, precision_rounding=rounding) < 0:
            available_quantity = sum(quants.mapped('reserved_quantity'))
            if available_quantity < abs(quantity):
                for quant in quants:
                    qty = abs(quantity) - available_quantity
                    quant.update({
                        'reserved_quantity': quant.reserved_quantity + qty
                    })
                    break
        if float_compare(quantity, 0, precision_rounding=rounding) > 0:
            # if we want to unreserve
            available_quantity = sum(quants.mapped('reserved_quantity'))
            if available_quantity < quantity:
                for quant in quants:
                    quant.update({
                        'reserved_quantity': -quantity
                    })
                    break
        return super(StockQuant, self)._update_reserved_quantity(product_id,location_id,quantity,lot_id,package_id,owner_id,strict)

