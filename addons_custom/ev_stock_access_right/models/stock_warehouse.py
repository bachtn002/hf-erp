# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID


class StockWarehouseInherit(models.Model):
    _inherit = 'stock.warehouse'

    user_ids = fields.Many2many('res.users', 'stock_warehouse_users_rel', 'warehouse_id', 'user_id',
                                string='Warehouse')

    out_minus = fields.Boolean('Out Minus', default=False)
    max_qty_process = fields.Float('Max quantity process', digits='Product Unit of Measure')

    def _get_warehouse_by_access_right(self):
        warehouse_ids = self.env['res.users'].sudo().search([('id', '=', self._uid)]).warehouse_ids
        if len(warehouse_ids) > 0:
            return warehouse_ids
        return False

    def _get_location_by_warehouse_access_right(self):
        location_ids = []
        warehouse_ids = self._get_warehouse_by_access_right()
        if warehouse_ids == False:
            return False
        for warehouse_id in warehouse_ids:
            loc_ids = self.env['stock.location']._get_location_children_ids(warehouse_id.view_location_id.id)
            if isinstance(loc_ids, list):
                for loc_id in loc_ids:
                    location_ids.append(loc_id)
            else:
                location_ids.append(loc_ids)
        return location_ids

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = [('name', operator, name)]
        access_right = []
        access_all = False
        if len(args) != 0:
            if args[0][0] == 'x_is_supply_warehouse':
                access_all = True
        # Check user root
        if self.env.uid == SUPERUSER_ID or self.env.user.has_group(
                'ev_stock_access_right.group_stock_access_all') or access_all == True:
            warehouse_ids = self._search(domain + args + access_right, limit=limit, access_rights_uid=name_get_uid)
            return self.browse(warehouse_ids).ids

        if access_all == False:
            warehouse_access_right_ids = self.env['stock.warehouse']._get_warehouse_by_access_right()
            if warehouse_access_right_ids != False:
                access_right = [('id', 'in', warehouse_access_right_ids.ids)]

        warehouse_ids = self._search(domain + args + access_right, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(warehouse_ids).ids

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.uid == SUPERUSER_ID or self.env.user.has_group('ev_stock_access_right.group_stock_access_all'):
            domain = domain
        else:
            warehouse_access_right_ids = self.env['stock.warehouse']._get_warehouse_by_access_right()
            warehouse_ids = warehouse_access_right_ids.ids
            domain_warehouse = []
            domain_warehouse.append('id')
            if len(warehouse_ids) == 1:
                domain_warehouse.append('=')
                listToStr = ' '.join(map(str, warehouse_ids))
                warehouse_id = int(listToStr)
                domain_warehouse.append(warehouse_id)
            else:
                domain_warehouse.append('in')
                domain_warehouse.append(warehouse_ids)
            domain.append(domain_warehouse)
        return super(StockWarehouseInherit, self).search_read(domain, fields, offset, limit, order)
