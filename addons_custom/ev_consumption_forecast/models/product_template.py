# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_min_stock = fields.Float('Min Stock', digits='Product Unit of Measure', default=0)
    x_moq_warehouse = fields.Float('MOQ Warehouse', digits='Product Unit of Measure', default=0)
    x_moq_purchase = fields.Float('MOQ Purchase', digits='Product Unit of Measure', default=0)
    x_lead_time = fields.Integer('Lead Time', default=0)
    x_order_multiples = fields.Integer('Order Multiples', default=0)
    x_order_schedule_ids = fields.Many2many('custom.weekdays', 'product_weekdays_rel', 'product_id', 'weekday_id',
                                            string='Order Schedule')
    x_user_id = fields.Text('Users')
    x_return_conditions = fields.Text('Return Conditions')
    x_min_stock_shop_ids = fields.One2many('min.stock.shop', 'product_tmpl_id', 'Min Stock Shop')

    @api.constrains('x_min_stock', 'x_moq_warehouse', 'x_moq_purchase', 'x_lead_time', 'x_order_multiples')
    def _check_fields_number(self):
        try:
            if self.x_min_stock < 0:
                raise UserError(_('Min Stock must be greater than 0'))
            if self.x_moq_warehouse < 0:
                raise UserError(_('MOQ Warehouse must be greater than 0'))
            if self.x_moq_purchase < 0:
                raise UserError(_('MOQ Purchase must be greater than 0'))
            if self.x_lead_time < 0:
                raise UserError(_('Lead Time must be greater than 0'))
            if self.x_order_multiples < 0:
                raise UserError(_('Order Multiples must be greater than 0'))
        except Exception as e:
            raise ValidationError(e)
