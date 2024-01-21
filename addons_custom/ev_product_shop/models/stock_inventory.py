# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    def _set_domain_product(self):
        try:
            domain = [('type', '=', 'product'), ('product_tmpl_id.active', '=', True)]
            if not self.env.user.x_view_all_shop:
                product_template_ids = self.env.user.x_pos_shop_ids.product_ids
                product_ids = self.env['product.product'].sudo().search(
                    [('product_tmpl_id', 'in', product_template_ids.ids)])
                domain = ['|', '&', '&', '&',
                          ('type', '=', 'product'),
                          ('product_tmpl_id.active', '=', True),
                          ('id', 'in', product_ids.ids),
                          ('product_tmpl_id.available_in_pos', '=', True),
                          '&', '&',
                          ('type', '=', 'product'),
                          ('product_tmpl_id.active', '=', True),
                          ('product_tmpl_id.x_is_tools', '=', True)
                          ]

            return domain
        except Exception as e:
            raise ValidationError(e)

    product_ids = fields.Many2many(
        'product.product', string='Products', check_company=True,
        domain=_set_domain_product,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Specify Products to focus your inventory on particular Products.")

    @api.onchange('x_location_id')
    def _onchange_product_id(self):
        try:
            domain = [('type', '=', 'product'), ('product_tmpl_id.active', '=', True)]
            if self.x_location_id:
                if not self.x_location_id.x_warehouse_id.x_is_supply_warehouse:
                    pos_shop = self.env['pos.shop'].sudo().search(
                        [('warehouse_id', '=', self.x_location_id.x_warehouse_id.id)])
                    product_ids = self.env['product.product'].search(
                        [('product_tmpl_id', 'in', pos_shop.product_ids.ids)])
                    domain = ['|', '&', '&', '&',
                              ('type', '=', 'product'),
                              ('product_tmpl_id.active', '=', True),
                              ('id', 'in', product_ids.ids),
                              ('product_tmpl_id.available_in_pos', '=', True),
                              '&', '&',
                              ('type', '=', 'product'),
                              ('product_tmpl_id.active', '=', True),
                              ('product_tmpl_id.x_is_tools', '=', True)
                              ]
            else:
                domain = self._set_domain_product()
            return {'domain': {'product_id': domain}}

        except Exception as e:
            raise ValidationError(e)

    @api.onchange('x_category_ids', 'x_inventory_group_ids')
    def onchange_category_inventory_group(self):
        try:
            # if not self.x_location_id:
            #     raise UserError(_('You have not selected location! Please choose location.'))

            if self.x_category_ids or self.x_inventory_group_ids:
                self.x_products_invisible = True

                pos_shop = self.env['pos.shop'].sudo().search(
                    [('warehouse_id', '=', self.x_location_id.x_warehouse_id.id)], limit=1)
                check_product_ids = self.env['product.product'].search(
                    ['|', ('categ_id', 'in', self.x_category_ids.ids),
                     ('product_tmpl_id', 'in', self.x_inventory_group_ids.product_ids.ids)])
                ids = []
                for product in check_product_ids:
                    if not self.x_location_id.x_warehouse_id.x_is_supply_warehouse:
                        if product.product_tmpl_id.x_is_tools and product.product_tmpl_id.active:
                            ids.append(product.id)
                        elif not product.product_tmpl_id.x_is_tools and product.product_tmpl_id.active and product.product_tmpl_id in pos_shop.product_ids:
                            if product.product_tmpl_id.available_in_pos:
                                ids.append(product.id)
                    else:
                        ids.append(product.id)
                product_ids = self.env['product.product'].search([('id', 'in', ids)])
                if product_ids:
                    self.product_ids = product_ids

            elif not self.x_category_ids and not self.x_inventory_group_ids:
                self.product_ids = None
                self.x_products_invisible = False

        except Exception as e:
            raise ValidationError(e)

    def _get_quantities(self):
        """Return quantities group by product_id, location_id, lot_id, package_id and owner_id

        :return: a dict with keys as tuple of group by and quantity as value
        :rtype: dict
        """
        self.ensure_one()
        if self.location_ids:
            domain_loc = [('id', 'child_of', self.location_ids.ids)]
        else:
            domain_loc = [('company_id', '=', self.company_id.id), ('usage', 'in', ['internal', 'transit'])]
        locations_ids = [l['id'] for l in self.env['stock.location'].search_read(domain_loc, ['id'])]

        pos_shop = self.env['pos.shop'].sudo().search(
            [('warehouse_id', '=', self.x_location_id.x_warehouse_id.id)])

        domain = ['|', '&', '&', '&', '&', '&',
                  ('company_id', '=', self.company_id.id),
                  ('product_tmpl_id.active', '=', True),
                  ('location_id', 'in', locations_ids),
                  ('quantity', '!=', '0'),
                  ('product_id.product_tmpl_id', 'in', pos_shop.product_ids.ids),
                  ('product_tmpl_id.available_in_pos', '=', True),
                  '&', '&', '&', '&',
                  ('company_id', '=', self.company_id.id),
                  ('product_tmpl_id.active', '=', True),
                  ('location_id', 'in', locations_ids),
                  ('quantity', '!=', '0'),
                  ('product_tmpl_id.x_is_tools', '=', True)
                  ]

        if self.x_location_id.x_warehouse_id.x_is_supply_warehouse:
            domain = [('company_id', '=', self.company_id.id),
                      ('quantity', '!=', '0'),
                      ('product_tmpl_id.active', '=', True),
                      ('location_id', 'in', locations_ids)]
        if self.product_ids:
            domain = expression.AND([domain, [('product_id', 'in', self.product_ids.ids)]])

        fields = ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id', 'quantity:sum']
        group_by = ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id']

        quants = self.env['stock.quant'].read_group(domain, fields, group_by, lazy=False)
        return {(
                    quant['product_id'] and quant['product_id'][0] or False,
                    quant['location_id'] and quant['location_id'][0] or False,
                    quant['lot_id'] and quant['lot_id'][0] or False,
                    quant['package_id'] and quant['package_id'][0] or False,
                    quant['owner_id'] and quant['owner_id'][0] or False):
                    quant['quantity'] for quant in quants
                }

    def _get_exhausted_inventory_lines_vals(self, non_exhausted_set):
        """Return the values of the inventory lines to create if the user
        wants to include exhausted products. Exhausted products are products
        without quantities or quantity equal to 0.

        :param non_exhausted_set: set of tuple (product_id, location_id) of non exhausted product-location
        :return: a list containing the `stock.inventory.line` values to create
        :rtype: list
        """
        self.ensure_one()
        if self.product_ids:
            product_ids = self.product_ids.ids
        else:
            pos_shop = self.env['pos.shop'].sudo().search(
                [('warehouse_id', '=', self.x_location_id.x_warehouse_id.id)])
            # product_ids = self.env['product.product'].search([('product_tmpl_id', 'in', pos_shop.product_ids.ids)])
            product_ids = self.env['product.product'].search_read([
                '|', '&', '&', '&',
                ('type', '=', 'product'),
                ('product_tmpl_id.active', '=', True),
                ('product_tmpl_id', 'in', pos_shop.product_ids.ids),
                ('product_tmpl_id.available_in_pos', '=', True),
                '&', '&',
                ('type', '=', 'product'),
                ('product_tmpl_id.active', '=', True),
                ('product_tmpl_id.x_is_tools', '=', True)
            ], ['id'])
            if self.x_location_id.x_warehouse_id.x_is_supply_warehouse:
                product_ids = self.env['product.product'].search_read([
                    ('type', '=', 'product'),
                    ('product_tmpl_id.active', '=', True)
                ], ['id'])
            product_ids = [p['id'] for p in product_ids]
        if self.location_ids:
            location_ids = self.location_ids.ids
        else:
            location_ids = self.env['stock.warehouse'].search(
                [('company_id', '=', self.company_id.id)]).lot_stock_id.ids

        vals = []
        for product_id in product_ids:
            for location_id in location_ids:
                if ((product_id, location_id) not in non_exhausted_set):
                    vals.append({
                        'inventory_id': self.id,
                        'product_id': product_id,
                        'location_id': location_id,
                        'theoretical_qty': 0
                    })
        return vals
