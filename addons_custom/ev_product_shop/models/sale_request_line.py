# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import ValidationError, UserError


class SaleRequestLine(models.Model):
    _inherit = 'sale.request.line'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        try:
            domain = [('type', 'in', ['product', 'consu']), ('product_tmpl_id.active', '=', True)]
            if self.sale_request_id.warehouse_id:
                pos_shop = self.env['pos.shop'].sudo().search(
                    [('warehouse_id', '=', self.sale_request_id.warehouse_id.id)])
                product_ids = self.env['product.product'].search([('product_tmpl_id', 'in', pos_shop.product_ids.ids)])

                if not self.sale_request_id.warehouse_id.x_is_supply_warehouse:
                    domain = ['|', '&', '&', '&',
                              ('type', 'in', ['product', 'consu']),
                              ('product_tmpl_id.active', '=', True),
                              ('id', 'in', product_ids.ids),
                              ('product_tmpl_id.available_in_pos', '=', True),
                              '&', '&',
                              ('type', 'in', ['product', 'consu']),
                              ('product_tmpl_id.active', '=', True),
                              ('product_tmpl_id.x_is_tools', '=', True)
                              ]

                if self.product_id:
                    moq = 0
                    supply_type = ''
                    if self.sale_request_id.warehouse_id.x_is_supply_warehouse:
                        query_warehouse = self._sql_warehouse(self.sale_request_id.warehouse_id.id, self.product_id.id)
                        self._cr.execute(query_warehouse)
                        warehouse = self._cr.dictfetchone()
                        if warehouse:
                            if warehouse['supply_type'] == 'stop_supply':
                                supply_type = 'stop_supply'
                            else:
                                supply_type = 'purchase'
                                moq = self.product_id.product_tmpl_id.x_moq_purchase
                        else:
                            if self.product_id.product_tmpl_id.x_supply_type == 'stop_supply':
                                supply_type = 'stop_supply'
                            else:
                                supply_type = 'purchase'
                                moq = self.product_id.product_tmpl_id.x_moq_purchase
                    else:
                        query_region = self._sql_region(self.sale_request_id.warehouse_id.x_stock_region_id.id,
                                                        self.product_id.id)
                        self._cr.execute(query_region)
                        region = self._cr.dictfetchone()
                        if region:
                            if region['supply_type'] == 'warehouse':
                                supply_type = 'warehouse'
                                moq = self.product_id.product_tmpl_id.x_moq_warehouse
                            elif region['supply_type'] == 'purchase':
                                supply_type = 'purchase'
                                moq = self.product_id.product_tmpl_id.x_moq_purchase
                            elif region['supply_type'] == 'stop_supply':
                                supply_type = 'stop_supply'
                        else:
                            query_warehouse = self._sql_warehouse(self.sale_request_id.warehouse_id.id,
                                                                  self.product_id.id)
                            self._cr.execute(query_warehouse)
                            warehouse = self._cr.dictfetchone()
                            if warehouse:
                                if warehouse['supply_type'] == 'warehouse':
                                    supply_type = 'warehouse'
                                    moq = self.product_id.product_tmpl_id.x_moq_warehouse
                                elif warehouse['supply_type'] == 'purchase':
                                    supply_type = 'purchase'
                                    moq = self.product_id.product_tmpl_id.x_moq_purchase
                                elif warehouse['supply_type'] == 'stop_supply':
                                    supply_type = 'stop_supply'
                            else:
                                if self.product_id.product_tmpl_id.x_supply_type == 'warehouse':
                                    supply_type = 'warehouse'
                                    moq = self.product_id.product_tmpl_id.x_moq_warehouse
                                elif self.product_id.product_tmpl_id.x_supply_type == 'purchase':
                                    supply_type = 'purchase'
                                    moq = self.product_id.product_tmpl_id.x_moq_purchase
                                elif self.product_id.product_tmpl_id.x_supply_type == 'stop_supply':
                                    supply_type = 'stop_supply'

                    shop_id = self.env['pos.shop'].sudo().search(
                        [('warehouse_id', '=', self.sale_request_id.warehouse_id.id)],
                        limit=1)
                    predicted_qty = self.env['request.forecast'].sudo().search(
                        [('shop_id', '=', shop_id.id), ('product_id', '=', self.product_id.id),
                         ('date', '=', self.sale_request_id.date_request)], limit=1).predicted_qty
                    self.moq = moq
                    self.supply_type = supply_type
                    self.qty_forecast = predicted_qty
                    self.qty = self.qty_forecast = predicted_qty

            else:
                raise UserError(_('You have not selected warehouse! Please choose warehouse.'))

            return {'domain': {'product_id': domain}}

        except Exception as e:
            raise ValidationError(e)
