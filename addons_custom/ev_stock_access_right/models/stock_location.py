# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID


class StockLocationInherit(models.Model):
    _inherit = 'stock.location'

    def _get_warehouse_id(self):
        for location in self:
            location_view_id = self._get_location_parent_id(location.id)
            warehouse_id = self.env['stock.warehouse'].search([('view_location_id', '=', location_view_id)], limit=1)
            if warehouse_id.id == False:
                return False
            else:
                return warehouse_id.id

    def _get_location_parent_id(self, id):
        location = self.browse(id)
        if location.location_id.id == False:
            return location.id
        self._get_location_parent_id(location.location_id)

    def _get_location_children_ids(self, location_id):
        location_list_ids = []
        location_ids = self.search([('location_id', '=', location_id)])
        if len(location_ids) <= 0:
            return location_list_ids
        for loc_id in location_ids:
            children_ids = self._get_location_children_ids(loc_id.id)
            location_list_ids.append(loc_id.id)
            if isinstance(children_ids, list):
                for item in children_ids:
                    location_list_ids.append(item)
            else:
                location_list_ids.append(children_ids)
        return location_list_ids

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if args is None:
            args = []
        access_all = False
        #
        for l in args:
            if l == 'All':
                access_all = True
                args.remove('All')
        # Check root and role
        if self.env.uid == SUPERUSER_ID or self.env.user.has_group('ev_stock_access_right.group_stock_access_all'):
            location_ids = self._search(['|', ('barcode', operator, name), ('complete_name', operator, name)] + args,
                                        limit=limit, access_rights_uid=name_get_uid)

            return self.browse(location_ids).ids

        if access_all == False:
            location_access_right_ids = self.env['stock.warehouse']._get_location_by_warehouse_access_right()
            domain = []
            domain.append('id')
            domain.append('in')
            domain.append(location_access_right_ids)
            args.append(domain)

        location_ids = self._search(['|', ('barcode', operator, name), ('complete_name', operator, name)] + args,
                                    limit=limit, access_rights_uid=name_get_uid)
        return self.browse(location_ids).ids

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.uid == SUPERUSER_ID or self.env.user.has_group('ev_stock_access_right.group_stock_access_all'):
            domain = domain
        else:
            location_access_right_ids = self.env['stock.warehouse']._get_location_by_warehouse_access_right()
            domain_location = []
            domain_location.append('id')
            if len(location_access_right_ids) == 1:
                domain_location.append('=')
                listToStr = ' '.join(map(str, location_access_right_ids))
                location_id = int(listToStr)
                domain_location.append(location_id)
            else:
                domain_location.append('in')
                domain_location.append(location_access_right_ids)
            domain.append(domain_location)
        return super(StockLocationInherit, self).search_read(domain, fields, offset, limit, order)
