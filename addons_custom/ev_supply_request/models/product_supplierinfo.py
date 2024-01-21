# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    x_listed_price = fields.Float('Listed Price', default=0)
    x_price_location = fields.Boolean('Price Location', default=False)
    x_region_ids = fields.Many2many('stock.region', 'price_stock_region', 'supplierinfo_id', 'region_id', string='Region')
    x_warehouse_ids = fields.Many2many('stock.warehouse', 'price_stock_warehouse', 'supplierinfo_id', 'warehouse_id', string='Warehouse')

    x_check_required = fields.Boolean('Check required region or warehouse', default=False)

    x_partner_ref = fields.Char('Partner Ref', related='name.ref')

    @api.onchange('x_price_location', 'x_region_ids', 'x_warehouse_ids')
    def _onchange_check_required(self):
        try:
            if self.x_price_location:
                if not self.x_warehouse_ids and not self.x_region_ids:
                    self.x_check_required = True
                else:
                    self.x_check_required = False
            else:
                self.x_check_required = False
        except Exception as e:
            raise ValidationError(e)
