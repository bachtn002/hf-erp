# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # x_supply_group_ids = fields.Many2many('supply.product.group', 'list_product_group_supply', 'product_id', 'group_id',
    #                                       string='List Group Supply')

    def _select_seller_location(self, partner_id=False, quantity=0.0, date=None, uom_id=False, params=False,
                                location=True, warehouse_id=False, region_id=False):
        self.ensure_one()
        if date is None:
            date = fields.Date.context_today(self)
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        res = self.env['product.supplierinfo']
        sellers = self._prepare_sellers_location(params)
        if location == False:
            sellers = self._prepare_sellers_no_location(params)
        sellers = sellers.filtered(lambda s: not s.company_id or s.company_id.id == self.env.company.id)
        for seller in sellers:
            # Set quantity in UoM of seller
            quantity_uom_seller = quantity
            if quantity_uom_seller and uom_id and uom_id != seller.product_uom:
                quantity_uom_seller = uom_id._compute_quantity(quantity_uom_seller, seller.product_uom)

            if seller.date_start and seller.date_start > date:
                continue
            if seller.date_end and seller.date_end < date:
                continue
            if partner_id and seller.name not in [partner_id, partner_id.parent_id]:
                continue
            if float_compare(quantity_uom_seller, seller.min_qty, precision_digits=precision) == -1:
                continue
            if seller.product_id and seller.product_id != self:
                continue
            if location == True:
                if warehouse_id.id not in seller.x_warehouse_ids.ids and region_id.id not in seller.x_region_ids.ids:
                    continue
            if not res or res.name == seller.name:
                res |= seller
        return res.sorted('price')[:1]

    def _prepare_sellers_location(self, params=False):
        # This search is made to avoid retrieving seller_ids from the cache.
        return self.env['product.supplierinfo'].search([('product_tmpl_id', '=', self.product_tmpl_id.id),
                                                        ('name.active', '=', True),
                                                        ('x_price_location', '=', True)]).sorted(
            lambda s: (s.sequence, -s.min_qty, s.price, s.id))

    def _prepare_sellers_no_location(self, params=False):
        # This search is made to avoid retrieving seller_ids from the cache.
        return self.env['product.supplierinfo'].search([('product_tmpl_id', '=', self.product_tmpl_id.id),
                                                        ('name.active', '=', True),
                                                        ('x_price_location', '=', False)]).sorted(
            lambda s: (s.sequence, -s.min_qty, s.price, s.id))
