# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SaleRequestLine(models.Model):
    _inherit = 'sale.request.line'

    moq = fields.Float('MOQ', digits='Product Unit of Measure', default=0, readonly=True)
    qty_forecast = fields.Float('Quantity Forecast', digits='Product Unit of Measure', default=0, readonly=True)

    @api.model
    def create(self, vals):
        try:
            res = super(SaleRequestLine, self).create(vals)
            if res.supply_type == 'warehouse':
                res.moq = res.product_id.product_tmpl_id.x_moq_warehouse
            elif res.supply_type == 'purchase':
                res.moq = res.product_id.product_tmpl_id.x_moq_purchase
            shop_id = self.env['pos.shop'].sudo().search([('warehouse_id', '=', res.sale_request_id.warehouse_id.id)],
                                                         limit=1)
            if not shop_id:
                return res

            predicted_qty = self.env['request.forecast'].sudo().search(
                [('shop_id', '=', shop_id.id), ('product_id', '=', res.product_id.id),
                 ('date', '=', res.sale_request_id.date_request)], limit=1).predicted_qty
            res.qty_forecast = predicted_qty
            return res
        except Exception as e:
            raise ValidationError(e)

    @api.model
    def write(self, vals):
        try:
            res = super(SaleRequestLine, self).write(vals)
            if 'product_id' in vals:
                product_id = self.env['product.product'].sudo().search([('id', '=', vals['product_id'])])
                if vals['supply_type'] == 'warehouse':
                    self.moq = product_id.product_tmpl_id.x_moq_warehouse
                elif vals['supply_type'] == 'purchase':
                    self.moq = product_id.product_tmpl_id.x_moq_purchase

                shop_id = self.env['pos.shop'].sudo().search(
                    [('warehouse_id', '=', self.sale_request_id.warehouse_id.id)],
                    limit=1)
                if not shop_id:
                    return res

                predicted_qty = self.env['request.forecast'].sudo().search(
                    [('shop_id', '=', shop_id.id), ('product_id', '=', self.product_id.id),
                     ('date', '=', self.sale_request_id.date_request)], limit=1).predicted_qty
                self.qty_forecast = predicted_qty
            return res
        except Exception as e:
            raise ValidationError(e)
