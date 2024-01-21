# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, SUPERUSER_ID


class PickingTypeInherit(models.Model):
    _inherit = "stock.picking.type"

    security_user_no_warehouse = fields.Boolean(default=False)

    # @api.model
    # def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
    #     args = args or []
    #     domain = []
    #     if name:
    #         domain = ['|', ('name', operator, name), ('warehouse_id.name', operator, name)]
    #     access_right = []
    #     #Check user root
    #     if self.env.uid == SUPERUSER_ID or self.env.user.has_group('ev_stock_access_right.group_stock_access_all'):
    #         picking_ids = self._search(domain + args + access_right, limit=limit, access_rights_uid=name_get_uid)
    #         return self.browse(picking_ids).name_get()
    #
    #     warehouse_access_right_ids = self.env['stock.warehouse']._get_warehouse_by_access_right()
    #     if warehouse_access_right_ids != False:
    #         access_right = [('warehouse_id', 'in', warehouse_access_right_ids.ids)]
    #
    #     picking_ids = self._search(domain + args + access_right, limit=limit, access_rights_uid=name_get_uid)
    #     return self.browse(picking_ids).name_get()


