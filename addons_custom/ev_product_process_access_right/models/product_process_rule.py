# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductProcessRule(models.Model):
    _inherit = "product.process.rule"

    apply_manual_warehouse = fields.Boolean(string=_('Apply manual warehouse'), default=False)
    apply_all_warehouse = fields.Boolean(string=_('Apply for all warehouse'), default=False)

    allow_warehouse_ids = fields.Many2many('stock.warehouse', 'product_process_rule_warehouse_rel', 'process_rule_id',
                                           'warehouse_id', string="Allow warehouses")

    @api.constrains('apply_manual_warehouse', 'apply_all_warehouse')
    def check_warehouse_apply(self):
        if self.apply_manual_warehouse and self.apply_all_warehouse:
            raise UserError(_('You can only choose one options for warehouse access right!'))





