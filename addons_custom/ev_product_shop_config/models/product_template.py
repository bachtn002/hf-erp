# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_pos_shop_ids = fields.Many2many('pos.shop', 'product_shop_rel', 'product_id', 'pos_shop_id',
                                      string='Pos Shop', copy=True)
    x_is_tools = fields.Boolean('Is Tools', default=False)

    @api.model
    def create(self, vals):
        try:
            res = super(ProductTemplate, self).create(vals)
            if 'available_in_pos' in vals and 'type' in vals:
                if vals['available_in_pos'] == True and vals['type'] != 'service':
                    query = """
                        select * from product_shop_rel where product_id = %s limit 1
                    """ % (res.id)
                    self._cr.execute(query)
                    values = self._cr.fetchone()
                    if not values:
                        raise ValueError(_('You can choose Shop'))
            return res
        except Exception as e:
            raise ValidationError(e)

    def write(self, vals):
        try:
            res = super(ProductTemplate, self).write(vals)
            if self.available_in_pos == True and self.type != 'service':
                query = """
                    select * from product_shop_rel where product_id = %s limit 1
                """ % (self.id)
                self._cr.execute(query)
                values = self._cr.fetchone()
                if not values:
                    raise ValueError(_('You can choose Shop'))

            return res
        except Exception as e:
            raise ValidationError(e)
