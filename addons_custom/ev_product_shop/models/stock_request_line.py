# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import ValidationError, UserError


class StockRequestLine(models.Model):
    _inherit = 'stock.request.line'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        try:
            domain = [('type', 'in', ['product', 'consu']), ('product_tmpl_id.active', '=', True)]
            if self.request_id.type == 'transfer':
                if self.request_id.warehouse_id:
                    if not self.request_id.warehouse_id.x_is_supply_warehouse:
                        pos_shop = self.env['pos.shop'].sudo().search(
                            [('warehouse_id', '=', self.request_id.warehouse_id.id)])
                        product_ids = self.env['product.product'].search(
                            [('product_tmpl_id', 'in', pos_shop.product_ids.ids)])
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
                else:
                    raise UserError(_('You have not selected warehouse! Please choose warehouse.'))

            if self.product_id:
                self.uom_id = self.product_id.product_tmpl_id.uom_id.id

            return {'domain': {'product_id': domain}}

        except Exception as e:
            raise ValidationError(e)
