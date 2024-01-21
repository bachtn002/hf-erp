# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api


class Product(models.Model):
    _inherit = 'product.product'

    @api.model
    def get_all_products_by_barcode(self):
        products = self.env['product.product'].search_read(
            [('barcode', '!=', None), ('type', '!=', 'service')],
            ['barcode', 'display_name', 'uom_id', 'tracking', 'is_package_cover']
        )
        packagings = self.env['product.packaging'].search_read(
            [('barcode', '!=', None), ('product_id', '!=', None)],
            ['barcode', 'product_id', 'qty']
        )
        multi_barcodes = self.env['product.barcode'].search_read([('product_id', '!=', False), ('active', '=', True)])
        # for each packaging, grab the corresponding product data
        to_add = []
        to_read = []
        products_by_id = {product['id']: product for product in products}
        for packaging in packagings:
            if products_by_id.get(packaging['product_id']):
                product = products_by_id[packaging['product_id']]
                to_add.append(dict(product, **{'qty': packaging['qty']}))
            # if the product doesn't have a barcode, you need to read it directly in the DB
            to_read.append((packaging, packaging['product_id'][0]))
        # get list product have multi barcode
        products_by_multi_barcode = [product['product_id'][0] for product in multi_barcodes]
        products_barcode = self.env['product.product'].search_read(
            [('id', 'in', products_by_multi_barcode)],
            ['barcode', 'display_name', 'uom_id', 'tracking'])
        # get list Barcode append with product and qty
        products_barcode_by_id = {product['id']: product for product in products_barcode}
        product_tracking_by_multi_barcode = {}
        for barcode in multi_barcodes:
            # get product by multi barcode
            product = products_barcode_by_id.get(barcode['product_id'][0])
            product.update({'qty': barcode['qty']})
            # Add barcode multi in front of product
            product_tracking_by_multi_barcode[barcode['name']] = product

        products_to_read = self.env['product.product'].browse(list(set(t[1] for t in to_read))).sudo().read(['display_name', 'uom_id', 'tracking'])
        products_to_read = {product['id']: product for product in products_to_read}
        to_add.extend([dict(t[0], **products_to_read[t[1]]) for t in to_read])

        products_results = {product.pop('barcode'): product for product in products + to_add}
        # merge two results
        results = {**products_results, **product_tracking_by_multi_barcode}
        return results
