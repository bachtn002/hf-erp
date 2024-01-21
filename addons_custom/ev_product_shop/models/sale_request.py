# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import ValidationError, UserError


class SaleRequest(models.Model):
    _inherit = 'sale.request'

    def send_sale_request(self):
        try:
            pos_shop = self.env['pos.shop'].sudo().search([('warehouse_id', '=', self.warehouse_id.id)])
            product_ids = self.env['product.product'].search([('product_tmpl_id', 'in', pos_shop.product_ids.ids)])

            list_product_errors = []
            for line in self.sale_request_line:
                if not self.warehouse_id.x_is_supply_warehouse:
                    if not line.product_id.product_tmpl_id.active:
                        list_product_errors.append(line.product_id.product_tmpl_id.name)
                        continue
                    if not line.product_id.product_tmpl_id.x_is_tools:
                        if line.product_id in product_ids:
                            if not line.product_id.product_tmpl_id.sale_ok:
                                list_product_errors.append(line.product_id.product_tmpl_id.name)
                            elif not line.product_id.product_tmpl_id.available_in_pos and line.product_id.product_tmpl_id.sale_ok:
                                list_product_errors.append(line.product_id.product_tmpl_id.name)
                        else:
                            list_product_errors.append(line.product_id.product_tmpl_id.name)
            mess_error = ' , '.join([str(err) for err in list_product_errors])
            if len(mess_error) > 0:
                raise UserError(_('Product can not send request : (%s)') % mess_error)
            return super(SaleRequest, self).send_sale_request()
        except Exception as e:
            raise ValidationError(e)

    def write(self, vals):
        if self.state != 'draft':
            if vals.get('date_request') or vals.get('warehouse_id') or vals.get('sale_request_line'):
                raise ValidationError(_("You can only edit in draft"))
        res = super(SaleRequest, self).write(vals)
        return res

