# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        try:
            self.analytic_account_id = self.warehouse_id.x_analytic_account_id
        except Exception as e:
            raise ValidationError(e)

    def action_confirm(self):
        try:
            res = super(SaleOrder, self).action_confirm()
            for picking_id in self.picking_ids:
                picking_id.x_analytic_account_id = self.analytic_account_id
            return res
        except Exception as e:
            raise ValidationError(e)
