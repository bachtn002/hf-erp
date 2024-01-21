# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class MinStockShop(models.Model):
    _name = 'min.stock.shop'

    pos_shop_id = fields.Many2one('pos.shop', 'Shop', required=True)
    product_tmpl_id = fields.Many2one('product.template', 'Product')
    min_stock = fields.Float('Min Stock', digits='Product Unit of Measure', default=0)


    @api.constrains('min_stock')
    def _check_min_stock(self):
        try:
            if self.min_stock < 0:
                raise UserError(_('Min Stock must be greater than 0'))
        except Exception as e:
            raise ValidationError(e)
