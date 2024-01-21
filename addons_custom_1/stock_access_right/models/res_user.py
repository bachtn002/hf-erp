# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    warehouse_ids = fields.Many2many('stock.warehouse', 'stock_warehouse_users_rel', 'user_id', 'warehouse_id', string='Warehouse')
    security_user_warehouse = fields.Boolean(default=False, compute='_compute_security_warehouse')

    @api.depends('warehouse_ids')
    def _compute_security_warehouse(self):
        for record in self:
            if record.warehouse_ids:
                record.security_user_warehouse = True
            else:
                if record.user_has_groups('ev_stock_access_right.group_stock_access_all'):
                    record.security_user_warehouse = False
