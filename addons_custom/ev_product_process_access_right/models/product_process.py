# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ProductProcess(models.Model):
    _inherit = 'product.process'

    rule_ids = fields.Many2many('product.process.rule', string='Rules')

    @api.onchange('location_id')
    def _onchange_process(self):
        self.rule_ids = False
        if self.location_id:
            warehouses = self.env['stock.warehouse'].search(
                [('active', '=', True), '|', ('lot_stock_id', '=', self.location_id.id),
                 ('view_location_id', '=', self.location_id.id)])
            rules_allow = self.env['product.process.rule'].search(['|', ('apply_all_warehouse', '=', True), ('allow_warehouse_ids', 'in', warehouses.ids)])
            self.rule_ids = rules_allow
